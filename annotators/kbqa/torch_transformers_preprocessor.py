# Copyright 2017 Neural Networks and Deep Learning lab, MIPT
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from logging import getLogger
import torch
from typing import List, Dict

from transformers import AutoTokenizer

from deeppavlov.core.common.registry import register
from deeppavlov.core.models.component import Component

log = getLogger(__name__)


@register("rel_ranking_preprocessor")
class RelRankingPreprocessor(Component):
    def __init__(
        self,
        vocab_file: str,
        add_special_tokens: List[str],
        do_lower_case: bool = True,
        max_seq_length: int = 512,
        return_tokens: bool = False,
        **kwargs,
    ) -> None:
        self.max_seq_length = max_seq_length
        self.return_tokens = return_tokens
        self.tokenizer = AutoTokenizer.from_pretrained(vocab_file, do_lower_case=do_lower_case)
        self.add_special_tokens = add_special_tokens

    def __call__(self, questions_batch: List[List[str]], rels_batch: List[List[str]] = None) -> Dict[str, torch.tensor]:
        lengths = []
        for question, rels_list in zip(questions_batch, rels_batch):
            if isinstance(rels_list, list):
                rels_str = self.add_special_tokens[2].join(rels_list)
            else:
                rels_str = rels_list
            text_input = f"{self.add_special_tokens[0]} {question} {self.add_special_tokens[1]} {rels_str}"
            encoding = self.tokenizer.encode_plus(
                text=text_input, return_attention_mask=True, add_special_tokens=True, truncation=True
            )
            lengths.append(len(encoding["input_ids"]))
        max_len = max(lengths)
        input_ids_batch = []
        attention_mask_batch = []
        token_type_ids_batch = []
        for question, rels_list in zip(questions_batch, rels_batch):
            if isinstance(rels_list, list):
                rels_str = self.add_special_tokens[2].join(rels_list)
            else:
                rels_str = rels_list
            text_input = f"{self.add_special_tokens[0]} {question} {self.add_special_tokens[1]} {rels_str}"
            encoding = self.tokenizer.encode_plus(
                text=text_input, truncation=True, max_length=max_len, pad_to_max_length=True, return_attention_mask=True
            )
            input_ids_batch.append(encoding["input_ids"])
            attention_mask_batch.append(encoding["attention_mask"])
            if "token_type_ids" in encoding:
                token_type_ids_batch.append(encoding["token_type_ids"])
            else:
                token_type_ids_batch.append([0])

        input_features = {
            "input_ids": torch.LongTensor(input_ids_batch),
            "attention_mask": torch.LongTensor(attention_mask_batch),
            "token_type_ids": torch.LongTensor(token_type_ids_batch),
        }

        return input_features
