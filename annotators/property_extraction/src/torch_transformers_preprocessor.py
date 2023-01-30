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
from pathlib import Path
from typing import List

from transformers import AutoTokenizer

from deeppavlov.core.commands.utils import expand_path
from deeppavlov.core.common.registry import register
from deeppavlov.core.models.component import Component

log = getLogger(__name__)


@register("t5_generative_ie_preprocessor")
class T5GenerativeIEPreprocessor(Component):
    def __init__(
        self,
        vocab_file: str,
        do_lower_case: bool = True,
        max_seq_length: int = 512,
        return_tokens: bool = False,
        add_special_tokens: List[str] = None,
        **kwargs,
    ) -> None:
        self.max_seq_length = max_seq_length
        self.return_tokens = return_tokens
        if Path(vocab_file).is_file():
            vocab_file = str(expand_path(vocab_file))
            self.tokenizer = AutoTokenizer(vocab_file=vocab_file, do_lower_case=do_lower_case)
        else:
            self.tokenizer = AutoTokenizer.from_pretrained(vocab_file, do_lower_case=do_lower_case)
        special_tokens_dict = {"additional_special_tokens": add_special_tokens}
        self.tokenizer.add_special_tokens(special_tokens_dict)

    def __call__(self, uttr_batch: List[str], targets_batch: List[str] = None):
        input_ids_batch, attention_mask_batch, lengths = [], [], []
        for uttr in uttr_batch:
            encoding = self.tokenizer.encode_plus(text=uttr, return_attention_mask=True, truncation=True)
            input_ids = encoding["input_ids"]
            attention_mask = encoding["attention_mask"]
            input_ids_batch.append(input_ids)
            attention_mask_batch.append(attention_mask)
            lengths.append(len(input_ids))
        max_length = min(max(lengths), self.max_seq_length)
        for i in range(len(input_ids_batch)):
            for _ in range(max_length - len(input_ids_batch[i])):
                input_ids_batch[i].append(0)
                attention_mask_batch[i].append(0)

        if targets_batch is None:
            return input_ids_batch, attention_mask_batch
        else:
            target_ids_batch, lengths = [], []
            for (subj, rel, obj) in targets_batch:
                target = f"<subj> {subj} <rel> {rel} <obj> {obj}"
                encoding = self.tokenizer.encode_plus(text=target, return_attention_mask=True, truncation=True)
                input_ids = encoding["input_ids"]
                target_ids_batch.append(input_ids)
                lengths.append(len(input_ids))
            max_length = max(lengths)
            for i in range(len(target_ids_batch)):
                for _ in range(max_length - len(target_ids_batch[i])):
                    target_ids_batch[i].append(0)

            return input_ids_batch, attention_mask_batch, target_ids_batch
