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

import re
from logging import getLogger
from string import punctuation
from typing import List

import pymorphy2

from deeppavlov.core.common.registry import register
from deeppavlov.core.models.component import Component

logger = getLogger(__name__)


@register("ru_tokenizer_filter")
class RussianTokenizerFilter(Component):
    def __init__(self, **kwargs):
        self.lemmatizer = pymorphy2.MorphAnalyzer()
        self.re_tokenizer = re.compile(r"[\w']+|[^\w ]")

    def __call__(self, text_batch: List[str]) -> List[List[str]]:
        ngrams_batch = []
        for text in text_batch:
            unigrams, bigrams, trigrams = self.make_ngrams(text)
            ngrams_batch.append(unigrams + bigrams + trigrams)

        return ngrams_batch

    def make_ngrams(self, text):
        text_tokens = re.findall(self.re_tokenizer, text.lower())
        text_tokens = [self.lemmatizer.parse(tok)[0].normal_form for tok in text_tokens]
        unigrams = []
        bigrams = []
        trigrams = []
        if len(text_tokens) > 2:
            for i in range(len(text_tokens) - 2):
                first_tok = text_tokens[i]
                second_tok = text_tokens[i + 1]
                third_tok = text_tokens[i + 2]
                first_tok_ok = False
                second_tok_ok = False
                third_tok_ok = False
                if first_tok not in punctuation:
                    if first_tok.isalpha() and not first_tok.isspace():
                        first_tok_ok = True
                    elif "-" in first_tok:
                        first_tok_split = first_tok.split("-")
                        if any([piece.isalpha() for piece in first_tok_split]):
                            first_tok_ok = True
                if second_tok not in punctuation:
                    if second_tok.isalpha() and not second_tok.isspace():
                        second_tok_ok = True
                    elif "-" in second_tok:
                        second_tok_split = second_tok.split("-")
                        if any([piece.isalpha() for piece in second_tok_split]):
                            second_tok_ok = True
                if third_tok not in punctuation:
                    if third_tok.isalpha() and not third_tok.isspace():
                        third_tok_ok = True
                    elif "-" in third_tok:
                        third_tok_split = third_tok.split("-")
                        if any([piece.isalpha() for piece in third_tok_split]):
                            third_tok_ok = True
                if first_tok_ok and first_tok not in self.sw:
                    unigrams.append(first_tok)
                if first_tok_ok and second_tok_ok and second_tok not in self.sw and first_tok != "и":
                    bigrams.append(f"{first_tok} {second_tok}")
                if first_tok_ok and second_tok_ok and third_tok_ok and third_tok not in self.sw and first_tok != "и":
                    trigrams.append(f"{first_tok} {second_tok} {third_tok}")

            prev_tok = text_tokens[-2]
            last_tok = text_tokens[-1]
            prev_tok_ok = False
            last_tok_ok = False
            if prev_tok not in punctuation:
                if prev_tok.isalpha() and not prev_tok.isspace():
                    prev_tok_ok = True
                elif "-" in prev_tok:
                    prev_tok_split = first_tok.split("-")
                    if any([piece.isalpha() for piece in prev_tok_split]):
                        prev_tok_ok = True
            if last_tok not in punctuation:
                if last_tok.isalpha() and not last_tok.isspace():
                    last_tok_ok = True
                elif "-" in last_tok:
                    last_tok_split = last_tok.split("-")
                    if any([piece.isalpha() for piece in last_tok_split]):
                        last_tok_ok = True
            if prev_tok_ok and prev_tok not in self.sw:
                unigrams.append(prev_tok)
            if last_tok_ok and last_tok not in self.sw:
                unigrams.append(last_tok)
            if prev_tok_ok and last_tok_ok and last_tok not in self.sw and prev_tok != "и":
                bigrams.append(f"{prev_tok} {last_tok}")

        elif len(text_tokens) == 2:
            first_tok = text_tokens[0]
            second_tok = text_tokens[1]
            first_tok_ok = False
            second_tok_ok = False
            if first_tok not in punctuation:
                if first_tok.isalpha() and not first_tok.isspace():
                    first_tok_ok = True
                elif "-" in first_tok:
                    first_tok_split = first_tok.split("-")
                    if any([piece.isalpha() for piece in first_tok_split]):
                        first_tok_ok = True
            if second_tok not in punctuation:
                if second_tok.isalpha() and not second_tok.isspace():
                    second_tok_ok = True
                elif "-" in second_tok:
                    second_tok_split = second_tok.split("-")
                    if any([piece.isalpha() for piece in second_tok_split]):
                        second_tok_ok = True
            if first_tok_ok and first_tok not in self.sw:
                unigrams.append(first_tok)
            if first_tok_ok and second_tok_ok and second_tok not in self.sw and first_tok != "и":
                bigrams.append(f"{first_tok} {second_tok}")

        elif len(text_tokens) == 1:
            first_tok = text_tokens[0]
            first_tok_ok = False
            if first_tok not in punctuation:
                if first_tok.isalpha() and not first_tok.isspace():
                    first_tok_ok = True
                elif "-" in first_tok:
                    first_tok_split = first_tok.split("-")
                    if any([piece.isalpha() for piece in first_tok_split]):
                        first_tok_ok = True
            if first_tok_ok and first_tok not in self.sw:
                unigrams.append(first_tok)

        return unigrams, bigrams, trigrams
