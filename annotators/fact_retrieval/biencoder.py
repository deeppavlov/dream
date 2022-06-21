import functools
import math
import random
from argparse import Namespace
from typing import Dict, List, Optional, Tuple, Union

import torch
from pytorch_lightning.core import LightningModule
from pytorch_lightning.utilities.distributed import rank_zero_info
from torch.utils.data import DataLoader
from transformers import (
    BertConfig,
    BertModel,
    BertTokenizerFast,
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
                labels.append(n == 0)

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

    @staticmethod
    def _normalize_query(text: str) -> str:
        if text.endswith("?"):
            return text[:-1]
        return text
