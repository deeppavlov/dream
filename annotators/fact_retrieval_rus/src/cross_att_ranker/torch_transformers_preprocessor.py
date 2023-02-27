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
from typing import List

from transformers import AutoTokenizer

from deeppavlov.core.common.registry import register
from deeppavlov.core.models.component import Component

log = getLogger(__name__)


@register("paragraph_ranking_preprocessor")
class ParagraphRankingPreprocessor(Component):
    def __init__(
        self,
        vocab_file: str,
        add_special_tokens: List[str],
        do_lower_case: bool = True,
        max_seq_length: int = 67,
        num_neg_samples: int = 499,
        **kwargs,
    ) -> None:
        self.max_seq_length = max_seq_length
        self.num_neg_samples = num_neg_samples
        self.tokenizer = AutoTokenizer.from_pretrained(vocab_file, do_lower_case=do_lower_case)
        self.add_special_tokens = add_special_tokens
        special_tokens_dict = {"additional_special_tokens": add_special_tokens}
        self.tokenizer.add_special_tokens(special_tokens_dict)

    def __call__(
        self, questions_batch: List[str], doc_ids_batch: List[List[List[str]]], par_batch: List[List[List[str]]]
    ):
        input_features_batch = []
        for question, doc_ids_list, par_list in zip(questions_batch, doc_ids_batch, par_batch):
            input_ids_list, attention_mask_list = [], []
            proc_par_list, lengths = [], []
            for par_name, par in zip(doc_ids_list, par_list):
                par_str = f"{par_name} <par> {par}"
                encoding = self.tokenizer.encode_plus(
                    text=question,
                    text_pair=par_str,
                    return_attention_mask=True,
                    add_special_tokens=True,
                    truncation=True,
                )
                lengths.append(len(encoding["input_ids"]))
                proc_par_list.append(par_str)
            max_len = min(max(lengths), self.max_seq_length)
            for par_str in proc_par_list:
                encoding = self.tokenizer.encode_plus(
                    text=question,
                    text_pair=par_str,
                    truncation=True,
                    max_length=max_len,
                    add_special_tokens=True,
                    pad_to_max_length=True,
                    return_attention_mask=True,
                )
                input_ids_list.append(encoding["input_ids"])
                attention_mask_list.append(encoding["attention_mask"])
            input_features = {"input_ids": input_ids_list, "attention_mask": attention_mask_list}
            input_features_batch.append(input_features)
        return input_features_batch
