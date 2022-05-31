import functools
import glob
import json
import pickle
import math
import random
from argparse import ArgumentParser, Namespace
from typing import Dict, Iterable, List, Optional, Tuple, Union

import torch
import torch.distributed as dist
import torch.nn.functional as F
from pytorch_lightning.core import LightningModule
from pytorch_lightning.utilities.distributed import rank_zero_info
from torch.utils.data import DataLoader
from transformers import (
    AdamW,
    BertConfig,
    BertModel,
    BertTokenizerFast,
    get_linear_schedule_with_warmup,
)

class BiEncoderModel(BertModel):
    def __init__(self, config: BertConfig, hparams: Namespace):
        super().__init__(config)

        self.hparams = hparams
        if getattr(hparams, "projection_dim_size", None) is not None:
            self.dense = torch.nn.Linear(config.hidden_size, hparams.projection_dim_size)
            self.layer_norm = torch.nn.LayerNorm(hparams.projection_dim_size, eps=config.layer_norm_eps)

        self.init_weights()

    def forward(self, *args, **kwargs) -> torch.Tensor:
        sequence_output = super().forward(*args, **kwargs)[0]
        cls_output = sequence_output[:, 0, :].contiguous()
        if getattr(self.hparams, "projection_dim_size", None) is not None:
            cls_output = self.layer_norm(self.dense(cls_output))

        return cls_output


class BiEncoder(LightningModule):
    def __init__(self, hparams: Optional[Union[Namespace, dict]]):
        super().__init__()

        if isinstance(hparams, dict):
            if "binary_passage" in hparams and hparams["binary_passage"]:
                hparams["binary"] = True
            hparams = Namespace(**hparams)
        
        self.hparams.update(vars(hparams))

        self.query_encoder = BiEncoderModel.from_pretrained(self.hparams.base_pretrained_model, hparams=self.hparams)
        self.passage_encoder = BiEncoderModel.from_pretrained(self.hparams.base_pretrained_model, hparams=self.hparams)

        self._num_passages_per_query = 1 + hparams.num_other_negatives + hparams.num_hard_negatives

    def setup(self, step: str) -> None:
        self._train_examples = list(self._load_data(self.hparams.train_file))
        rank_zero_info("The number of training examples: %d", len(self._train_examples))
        self._eval_examples = list(self._load_data(self.hparams.eval_file))
        rank_zero_info("The number of eval examples: %d", len(self._eval_examples))

    def train_dataloader(self) -> DataLoader:
        collate_fn = functools.partial(
            BiEncoder._collate_fn,
            hparams=self.hparams,
            num_hard_negatives=self.hparams.num_hard_negatives,
            num_other_negatives=self.hparams.num_other_negatives,
            fold="train",
        )
        return DataLoader(
            self._train_examples,
            batch_size=self.hparams.train_batch_size,
            shuffle=True,
            num_workers=self.hparams.num_dataloader_workers,
            collate_fn=collate_fn,
            pin_memory=True,
            worker_init_fn=functools.partial(BiEncoder._init_worker, hparams=self.hparams),
        )

    def val_dataloader(self) -> List[DataLoader]:
        dataloader_loss = DataLoader(
            self._eval_examples,
            batch_size=self.hparams.eval_batch_size,
            num_workers=self.hparams.num_dataloader_workers,
            collate_fn=functools.partial(
                BiEncoder._collate_fn,
                hparams=self.hparams,
                num_hard_negatives=self.hparams.num_hard_negatives,
                num_other_negatives=self.hparams.num_other_negatives,
                fold="eval",
            ),
            pin_memory=True,
            worker_init_fn=functools.partial(BiEncoder._init_worker, hparams=self.hparams),
        )

        if self.current_epoch < self.hparams.eval_rank_start_epoch:
            return dataloader_loss

        eval_rank_examples = self._eval_examples
        if self.hparams.eval_rank_max_queries is not None:
            eval_rank_examples = eval_rank_examples[: self.hparams.eval_rank_max_queries]

        dataloader_rank = DataLoader(
            eval_rank_examples,
            batch_size=self.hparams.eval_rank_batch_size,
            num_workers=self.hparams.num_dataloader_workers,
            collate_fn=functools.partial(
                BiEncoder._collate_fn,
                hparams=self.hparams,
                num_hard_negatives=self.hparams.eval_rank_num_hard_negatives,
                num_other_negatives=self.hparams.eval_rank_num_other_negatives,
                fold="eval",
                include_passage_label=True,
            ),
            pin_memory=True,
            worker_init_fn=functools.partial(BiEncoder._init_worker, hparams=self.hparams),
        )
        return [dataloader_loss, dataloader_rank]

    @classmethod
    def _init_worker(cls, worker_id, hparams) -> None:
        cls.tokenizer = BertTokenizerFast.from_pretrained(hparams.base_pretrained_model)

    @classmethod
    def _collate_fn(
        cls,
        batch: list,
        hparams: Namespace,
        num_hard_negatives: int,
        num_other_negatives: int,
        fold: str,
        include_passage_label: bool = False,
    ) -> Dict[str, Union[Dict[str, torch.Tensor], torch.Tensor]]:
        queries = []
        passages = []
        labels = []

        for item in batch:
            query_text = cls._normalize_query(item["question"])
            encoded_query = cls.tokenizer.encode_plus(
                query_text, padding=False, truncation=True, max_length=hparams.max_query_length
            )
            queries.append(encoded_query)

            if fold == "train" and hparams.shuffle_positives:
                positive_passage = random.choice(item["positive_ctxs"])
            else:
                positive_passage = item["positive_ctxs"][0]

            hard_negative_passages = item["hard_negative_ctxs"]
            other_negative_passages = item["negative_ctxs"]

            if fold == "train":
                random.shuffle(hard_negative_passages)
                random.shuffle(other_negative_passages)

            negative_passages = hard_negative_passages[0:num_hard_negatives]
            negative_passages += other_negative_passages[0:num_other_negatives]

            while len(negative_passages) != num_hard_negatives + num_other_negatives:
                negative_passages.append(random.choice(hard_negative_passages + other_negative_passages))

            for n, passage in enumerate([positive_passage] + negative_passages):
                passages.append(
                    cls.tokenizer.encode_plus(
                        passage["title"],
                        passage["text"],
                        padding=False,
                        truncation=True,
                        max_length=hparams.max_passage_length,
                    )
                )
                labels.append(n==0)

        def create_padded_sequence(key: str, items: list) -> torch.Tensor:
            padding_value = 0
            if key == "input_ids":
                padding_value = cls.tokenizer.pad_token_id
            tensors = [torch.tensor(o[key], dtype=torch.long) for o in items]
            return torch.nn.utils.rnn.pad_sequence(tensors, batch_first=True, padding_value=padding_value)

        ret = dict(
            query_input={k: create_padded_sequence(k, queries) for k in queries[0].keys()},
            passage_input={k: create_padded_sequence(k, passages) for k in passages[0].keys()},
        )

        if include_passage_label:
            ret["passage_label"] = torch.tensor(labels, dtype=torch.long)

        return ret


    def forward(
        self, query_input: Dict[str, torch.LongTensor], passage_input: Dict[str, torch.LongTensor]
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        query_repr = self.query_encoder(**query_input)
        passage_repr = self.passage_encoder(**passage_input)
        return query_repr, passage_repr

    def convert_to_binary_code(self, input_repr: torch.Tensor) -> torch.Tensor:
        if self.training:
            if self.hparams.use_ste:
                hard_input_repr = input_repr.new_ones(input_repr.size()).masked_fill_(input_repr < 0, -1.0)
                input_repr = torch.tanh(input_repr)
                return hard_input_repr + input_repr - input_repr.detach()
            else:
                # https://github.com/thuml/HashNet/blob/55bcaaa0bbaf0c404ca7a071b47d6287dc95e81d/pytorch/src/network.py#L40
                scale = math.pow((1.0 + self.global_step * self.hparams.hashnet_gamma), 0.5)
                return torch.tanh(input_repr * scale)
        else:
            return input_repr.new_ones(input_repr.size()).masked_fill_(input_repr < 0, -1.0)

    def training_step(self, batch: Dict[str, torch.Tensor], batch_idx: int) -> dict:
        ret = self._compute_loss(batch)
        return dict(loss=ret["loss"], log={"train_" + k: v for k, v in ret.items()})

    def validation_step(
        self, batch: Dict[str, torch.Tensor], batch_idx: int, dataloader_idx: Optional[int] = None
    ) -> dict:
        if dataloader_idx == 1:
            label = batch.pop("passage_label")
            query_repr, passage_repr = self(**batch)
            return dict(query_repr=query_repr, passage_repr=passage_repr, label=label)
        else:
            return {"val_" + k: v for k, v in self._compute_loss(batch).items()}

    def validation_epoch_end(self, outputs: Union[List[dict], List[List[dict]]]) -> dict:
        if isinstance(outputs[0], dict):
            loss = torch.stack([x["val_loss"] for x in outputs]).mean()
            return dict(log=dict(val_loss=loss, val_avg_rank=loss.new_tensor(10000.0)))
        else:
            loss = torch.stack([x["val_loss"] for x in outputs[0]]).mean()

            query_repr = torch.cat([x["query_repr"] for x in outputs[1]], dim=0)
            passage_repr = torch.cat([x["passage_repr"] for x in outputs[1]], dim=0)
            label = torch.cat([x["label"] for x in outputs[1]])

            if self.use_ddp and not self.hparams.eval_rank_local_gpu:
                query_repr_list = [torch.empty_like(query_repr) for _ in range(dist.get_world_size())]
                dist.all_gather(query_repr_list, query_repr)
                query_repr = torch.cat(query_repr_list, dim=0)

                passage_repr_list = [torch.empty_like(passage_repr) for _ in range(dist.get_world_size())]
                dist.all_gather(passage_repr_list, passage_repr)
                passage_repr = torch.cat(passage_repr_list, dim=0)

                label_list = [torch.empty_like(label) for _ in range(dist.get_world_size())]
                dist.all_gather(label_list, label)
                label = torch.cat(label_list)

            if self.hparams.binary:
                passage_repr = self.convert_to_binary_code(passage_repr)

            avg_rank = self._compute_average_rank(query_repr, passage_repr, label)
            if self.use_ddp and self.hparams.eval_rank_local_gpu:
                avg_rank_list = [torch.empty_like(avg_rank) for _ in range(dist.get_world_size())]
                dist.all_gather(avg_rank_list, avg_rank)
                avg_rank = torch.stack(avg_rank_list).mean()

            return dict(log=dict(val_loss=loss, val_avg_rank=avg_rank))

    def _compute_loss(self, batch: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        query_repr, passage_repr = self(**batch)
        
        
        if self.use_ddp:
            query_repr_list = [torch.empty_like(query_repr) for _ in range(dist.get_world_size())]
            dist.all_gather(query_repr_list, query_repr)
            query_repr_list[dist.get_rank()] = query_repr
            query_repr = torch.cat(query_repr_list, dim=0)

            passage_repr_list = [torch.empty_like(passage_repr) for _ in range(dist.get_world_size())]
            dist.all_gather(passage_repr_list, passage_repr)
            passage_repr_list[dist.get_rank()] = passage_repr
            passage_repr = torch.cat(passage_repr_list, dim=0)

        if self.hparams.binary:
            passage_repr = self.convert_to_binary_code(passage_repr)
        
        labels = torch.arange(0, query_repr.size(0) * self._num_passages_per_query, self._num_passages_per_query)
        labels = labels.to(query_repr.device)

        similarity_scores = torch.matmul(query_repr, passage_repr.transpose(0, 1))
        dense_loss = kldivloss(similarity_scores, attention_scores)
        ret = dict(dense_loss=dense_loss)

        if self.hparams.binary:
            binary_query_repr = self.convert_to_binary_code(query_repr)
            binary_query_scores = torch.matmul(binary_query_repr, passage_repr.transpose(0, 1))
            if self.hparams.use_binary_cross_entropy_loss:
                binary_loss = F.cross_entropy(binary_query_scores, labels)
            else:            
                pos_mask = binary_query_scores.new_zeros(binary_query_scores.size(), dtype=torch.bool)
                for n, label in enumerate(labels):
                    pos_mask[n, label] = True
                pos_bin_scores = torch.masked_select(binary_query_scores, pos_mask)
                pos_bin_scores = pos_bin_scores.repeat_interleave(passage_repr.size(0) - 1)
                neg_bin_scores = torch.masked_select(binary_query_scores, torch.logical_not(pos_mask))
                bin_labels = pos_bin_scores.new_ones(pos_bin_scores.size(), dtype=torch.int64)
                binary_loss = F.margin_ranking_loss(
                    pos_bin_scores, neg_bin_scores, bin_labels, self.hparams.binary_ranking_loss_margin,
                )

            ret["binary_loss"] = binary_loss
            if self.hparams.no_binary_loss:
                ret["loss"] = dense_loss
            elif self.hparams.no_dense_loss:
                ret["loss"] = binary_loss 
            else:
                ret["loss"] = binary_loss + dense_loss
        else:
            ret["loss"] = dense_loss

        return ret

    def _compute_average_rank(
        self, query_repr: torch.Tensor, passage_repr: torch.Tensor, label: torch.Tensor
    ) -> torch.Tensor:
        if self.trainer.local_rank != 0 and not self.hparams.eval_rank_local_gpu:
            return torch.tensor(0.0, device=self.device)

        gold_positions = label.nonzero(as_tuple=False).view(-1).cpu()
        scores = torch.matmul(query_repr.cpu(), passage_repr.transpose(0, 1).cpu())
        gold_scores = scores.gather(1, gold_positions.unsqueeze(1))
        average_rank = (scores > gold_scores).sum(1).float().mean()
        return average_rank.to(self.device)

    def configure_optimizers(self) -> Tuple[list, list]:
        param_optimizer = list(self.named_parameters())
        no_decay = ["bias", "LayerNorm.weight"]
        optimizer_parameters = [
            {
                "params": [p for n, p in param_optimizer if p.requires_grad and not any(nd in n for nd in no_decay)],
                "weight_decay": self.hparams.weight_decay,
            },
            {
                "params": [p for n, p in param_optimizer if p.requires_grad and any(nd in n for nd in no_decay)],
                "weight_decay": 0.0,
            },
        ]
        self.optimizer = AdamW(optimizer_parameters, lr=self.hparams.learning_rate)
        num_training_steps = int(
            len(self._train_examples)
            // (self.hparams.train_batch_size * self.trainer.num_gpus)
            // self.hparams.accumulate_grad_batches
            * float(self.hparams.max_epochs)
        )
        rank_zero_info("The total number of training steps: %d", num_training_steps)

        warmup_steps = int(self.hparams.warmup_proportion * num_training_steps)

        self.scheduler = get_linear_schedule_with_warmup(
            self.optimizer, num_warmup_steps=warmup_steps, num_training_steps=num_training_steps
        )
        return [self.optimizer], [dict(scheduler=self.scheduler, interval="step")]

    @staticmethod
    def add_model_specific_args(parent_parser: ArgumentParser, root_dir: str) -> ArgumentParser:
        parser = ArgumentParser(parents=[parent_parser])

        parser.add_argument("--base_pretrained_model", default="DeepPavlov/bert-base-uncased")
        parser.add_argument("--binary", action="store_true")
        parser.add_argument("--binary_ranking_loss_margin", default=0.1, type=float)
        parser.add_argument("--eval_batch_size", default=10, type=int)
        parser.add_argument("--eval_file", default="data/retriever/nq-dev.json", type=str)
        parser.add_argument("--eval_rank_batch_size", default=2, type=int)
        parser.add_argument("--eval_rank_local_gpu", action="store_true")
        parser.add_argument("--eval_rank_max_queries", default=None, type=int)
        parser.add_argument("--eval_rank_num_hard_negatives", default=20, type=int)
        parser.add_argument("--eval_rank_num_other_negatives", default=20, type=int)
        parser.add_argument("--eval_rank_start_epoch", default=30, type=int)
        parser.add_argument("--hashnet_gamma", default=0.1, type=float)
        parser.add_argument("--learning_rate", default=2e-5, type=float)
        parser.add_argument("--max_passage_length", default=256, type=int)
        parser.add_argument("--max_query_length", default=256, type=int)
        parser.add_argument("--no_binary_loss", action="store_true")
        parser.add_argument("--no_dense_loss", action="store_true")
        parser.add_argument("--num_dataloader_workers", default=4, type=int)
        parser.add_argument("--num_hard_negatives", default=1, type=int)
        parser.add_argument("--num_other_negatives", default=0, type=int)
        parser.add_argument("--projection_dim_size", default=None, type=int)
        parser.add_argument("--shuffle_positives", action="store_true")
        parser.add_argument("--train_batch_size", default=10, type=int)
        parser.add_argument("--train_file", action="append", required=True)
        parser.add_argument("--use_ste", action="store_true")
        parser.add_argument("--use_binary_cross_entropy_loss", action="store_true")
        parser.add_argument("--warmup_proportion", default=0.06, type=float)
        parser.add_argument("--weight_decay", default=0.0, type=float)

        return parser

    def _load_data(self, paths: Union[str, list]) -> Iterable[dict]:
        if isinstance(paths, str):
            paths = [paths]

        for path in paths:
            for path in glob.glob(path):
                if path.endswith("json"):
                    with open(path) as f:
                        for item in json.load(f):
                            if len(item["positive_ctxs"]) == 0:
                                continue
                            if len(item["negative_ctxs"]) + len(item["hard_negative_ctxs"]) == 0:
                                continue
                            yield item
                if path.endswith(".pickle"):
                    with open(path, "rb") as f:
                        for item in pickle.load(f):
                            if len(item["positive_ctxs"]) == 0:
                                continue
                            if len(item["negative_ctxs"]) + len(item["hard_negative_ctxs"]) == 0:
                                continue
                            yield item

    @staticmethod
    def _normalize_query(text: str) -> str:
        if text.endswith("?"):
            return text[:-1]
        return text
