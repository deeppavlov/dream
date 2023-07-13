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
from typing import Tuple, List, Union

from transformers import AutoTokenizer
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
        **kwargs
    ) -> None:
        self.max_seq_length = max_seq_length
        self.return_tokens = return_tokens
        if Path(vocab_file).is_file():
            vocab_file = str(expand_path(vocab_file))
            self.tokenizer = AutoTokenizer(
                vocab_file=vocab_file, do_lower_case=do_lower_case
            )
        else:
            self.tokenizer = AutoTokenizer.from_pretrained(
                vocab_file, do_lower_case=do_lower_case
            )
        if special_tokens is not None:
            special_tokens_dict = {"additional_special_tokens": special_tokens}
            self.tokenizer.add_special_tokens(special_tokens_dict)

    def __call__(
        self, texts_a: List[str]
    ) -> Union[
        List[InputFeatures], Tuple[List[InputFeatures], List[List[str]]]
    ]:
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
