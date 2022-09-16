from pathlib import Path
from logging import getLogger
from typing import List, Tuple, Union

import torch
from transformers import AutoTokenizer, AutoModel
from transformers.data.processors.utils import InputFeatures

from deeppavlov.core.commands.utils import expand_path
from deeppavlov.core.common.registry import register
from deeppavlov.core.models.component import Component

log = getLogger(__name__)


@register("torch_transformers_entity_ranker_preprocessor")
class TorchTransformersEntityRankerPreprocessor(Component):
    def __init__(
        self,
        vocab_file: str,
        do_lower_case: bool = True,
        max_seq_length: int = 512,
        return_tokens: bool = False,
        special_tokens: List[str] = None,
        **kwargs,
    ) -> None:
        self.max_seq_length = max_seq_length
        self.return_tokens = return_tokens
        if Path(vocab_file).is_file():
            vocab_file = str(expand_path(vocab_file))
            self.tokenizer = AutoTokenizer(vocab_file=vocab_file, do_lower_case=do_lower_case)
        else:
            self.tokenizer = AutoTokenizer.from_pretrained(vocab_file, do_lower_case=do_lower_case)
        if special_tokens is not None:
            special_tokens_dict = {"additional_special_tokens": special_tokens}
            self.tokenizer.add_special_tokens(special_tokens_dict)

    def __call__(self, texts_a: List[str]) -> Union[List[InputFeatures], Tuple[List[InputFeatures], List[List[str]]]]:
        # in case of iterator's strange behaviour
        if isinstance(texts_a, tuple):
            texts_a = list(texts_a)
        lengths = []
        for text_a in texts_a:
            encoding = self.tokenizer.encode_plus(
                text_a,
                add_special_tokens=True,
                pad_to_max_length=True,
                return_attention_mask=True,
            )
            input_ids = encoding["input_ids"]
            lengths.append(len(input_ids))

        input_features = self.tokenizer(
            text=texts_a,
            add_special_tokens=True,
            max_length=self.max_seq_length,
            padding="max_length",
            return_attention_mask=True,
            truncation=True,
            return_tensors="pt",
        )
        return input_features


@register("torch_transformers_entity_ranker_infer")
class TorchTransformersEntityRankerInfer:
    def __init__(
        self,
        pretrained_bert,
        text_encoder_weights_path,
        descr_encoder_weights_path,
        special_token_id: int = 30522,
        do_lower_case: bool = True,
        batch_size: int = 5,
        descr_batch_size: int = 30,
        device: str = "gpu",
        **kwargs,
    ):
        self.device = torch.device("cuda" if torch.cuda.is_available() and device == "gpu" else "cpu")
        self.pretrained_bert = str(expand_path(pretrained_bert))
        self.preprocessor = TorchTransformersEntityRankerPreprocessor(
            vocab_file=self.pretrained_bert,
            do_lower_case=do_lower_case,
            special_tokens=["[ent]"],
        )
        self.text_encoder = AutoModel.from_pretrained(self.pretrained_bert)
        tokenizer = AutoTokenizer.from_pretrained(self.pretrained_bert)
        self.text_encoder.resize_token_embeddings(len(tokenizer) + 1)
        self.descr_encoder = AutoModel.from_pretrained(self.pretrained_bert)
        self.text_encoder_weights_path = str(expand_path(text_encoder_weights_path))
        text_encoder_checkpoint = torch.load(self.text_encoder_weights_path, map_location=self.device)
        self.text_encoder.load_state_dict(text_encoder_checkpoint["model_state_dict"])
        self.text_encoder.to(self.device)
        self.descr_encoder_weights_path = str(expand_path(descr_encoder_weights_path))
        descr_encoder_checkpoint = torch.load(self.descr_encoder_weights_path, map_location=self.device)
        self.descr_encoder.load_state_dict(descr_encoder_checkpoint["model_state_dict"])
        self.descr_encoder.to(self.device)
        self.special_token_id = special_token_id
        self.batch_size = batch_size
        self.descr_batch_size = descr_batch_size

    def __call__(
        self,
        contexts_batch: List[str],
        candidate_entities_batch: List[List[str]],
        candidate_entities_descr_batch: List[List[str]],
    ):
        entity_embs = []
        num_batches = len(contexts_batch) // self.batch_size + int(len(contexts_batch) % self.batch_size > 0)
        for ii in range(num_batches):
            contexts_list = contexts_batch[ii * self.batch_size : (ii + 1) * self.batch_size]
            context_features = self.preprocessor(contexts_list)
            text_input_ids = context_features["input_ids"].to(self.device)
            text_attention_mask = context_features["attention_mask"].to(self.device)
            entity_tokens_pos = []
            for input_ids_list in text_input_ids:
                found_n = -1
                for n, input_id in enumerate(input_ids_list):
                    if input_id == self.special_token_id:
                        found_n = n
                        break
                if found_n == -1:
                    found_n = 0
                entity_tokens_pos.append(found_n)

            text_encoder_output = self.text_encoder(input_ids=text_input_ids, attention_mask=text_attention_mask)
            text_hidden_states = text_encoder_output.last_hidden_state
            for i in range(len(entity_tokens_pos)):
                pos = entity_tokens_pos[i]
                entity_embs.append(text_hidden_states[i, pos].detach().cpu().numpy().tolist())

        scores_batch = []
        for entity_emb, candidate_entities_list, candidate_entities_descr_list in zip(
            entity_embs, candidate_entities_batch, candidate_entities_descr_batch
        ):
            if candidate_entities_list:
                num_batches = len(candidate_entities_descr_list) // self.descr_batch_size + int(
                    len(candidate_entities_descr_list) % self.descr_batch_size > 0
                )
                scores_list = []
                for jj in range(num_batches):
                    cur_descr_list = candidate_entities_descr_list[
                        jj * self.descr_batch_size : (jj + 1) * self.descr_batch_size
                    ]
                    entity_emb_list = [entity_emb for _ in cur_descr_list]
                    entity_emb_t = torch.Tensor(entity_emb_list).to(self.device)
                    descr_features = self.preprocessor(cur_descr_list)
                    descr_input_ids = descr_features["input_ids"].to(self.device)
                    descr_attention_mask = descr_features["attention_mask"].to(self.device)
                    descr_encoder_output = self.descr_encoder(
                        input_ids=descr_input_ids, attention_mask=descr_attention_mask
                    )
                    descr_cls_emb = descr_encoder_output.last_hidden_state[:, :1, :].squeeze(1)

                    bs, emb_dim = entity_emb_t.size()
                    entity_emb_t = entity_emb_t.reshape(bs, 1, emb_dim)
                    descr_cls_emb = descr_cls_emb.reshape(bs, emb_dim, 1)
                    dot_products = torch.matmul(entity_emb_t, descr_cls_emb).squeeze(1).squeeze(1)
                    cur_scores_list = dot_products.detach().cpu().numpy().tolist()
                    scores_list += cur_scores_list

                entities_with_scores = [
                    (entity, round(min(max(score - 114.0, 0.0), 28.0) / 28.0, 3))
                    for entity, score in zip(candidate_entities_list, scores_list)
                ]
                entities_with_scores = sorted(entities_with_scores, key=lambda x: x[1], reverse=True)
                scores_batch.append(entities_with_scores)
            else:
                scores_batch.append([])

        return scores_batch
