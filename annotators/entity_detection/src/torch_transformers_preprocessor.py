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
import random
from pathlib import Path
from logging import getLogger
from typing import Tuple, List, Union

from transformers import AutoTokenizer

from deeppavlov.core.commands.utils import expand_path
from deeppavlov.core.common.registry import register
from deeppavlov.core.data.utils import zero_pad
from deeppavlov.core.models.component import Component
from deeppavlov.models.preprocessors.mask import Mask

log = getLogger(__name__)


@register("torch_transformers_ner_preprocessor")
class TorchTransformersNerPreprocessor(Component):
    """
    Takes tokens and splits them into bert subtokens, encodes subtokens with their indices.
    Creates a mask of subtokens (one for the first subtoken, zero for the others).

    If tags are provided, calculates tags for subtokens.

    Args:
        vocab_file: path to vocabulary
        do_lower_case: set True if lowercasing is needed
        max_seq_length: max sequence length in subtokens, including [SEP] and [CLS] tokens
        max_subword_length: replace token to <unk> if it's length is larger than this
            (defaults to None, which is equal to +infinity)
        token_masking_prob: probability of masking token while training
        provide_subword_tags: output tags for subwords or for words
        subword_mask_mode: subword to select inside word tokens, can be "first" or "last"
            (default="first")

    Attributes:
        max_seq_length: max sequence length in subtokens, including [SEP] and [CLS] tokens
        max_subword_length: rmax lenght of a bert subtoken
        tokenizer: instance of Bert FullTokenizer
    """

    def __init__(
        self,
        vocab_file: str,
        do_lower_case: bool = False,
        max_seq_length: int = 512,
        max_subword_length: int = None,
        token_masking_prob: float = 0.0,
        provide_subword_tags: bool = False,
        subword_mask_mode: str = "first",
        **kwargs,
    ):
        self._re_tokenizer = re.compile(r"[\w']+|[^\w ]")
        self.provide_subword_tags = provide_subword_tags
        self.mode = kwargs.get("mode")
        self.max_seq_length = max_seq_length
        self.max_subword_length = max_subword_length
        self.subword_mask_mode = subword_mask_mode
        if Path(vocab_file).is_file():
            vocab_file = str(expand_path(vocab_file))
            self.tokenizer = AutoTokenizer(vocab_file=vocab_file, do_lower_case=do_lower_case)
        else:
            self.tokenizer = AutoTokenizer.from_pretrained(vocab_file, do_lower_case=do_lower_case)
        self.token_masking_prob = token_masking_prob

    def __call__(self, tokens: Union[List[List[str]], List[str]], tags: List[List[str]] = None, **kwargs):
        tokens_offsets_batch = [[] for _ in tokens]
        if isinstance(tokens[0], str):
            tokens_batch = []
            tokens_offsets_batch = []
            for s in tokens:
                tokens_list = []
                tokens_offsets_list = []
                for elem in re.finditer(self._re_tokenizer, s):
                    tokens_list.append(elem[0])
                    tokens_offsets_list.append((elem.start(), elem.end()))
                tokens_batch.append(tokens_list)
                tokens_offsets_batch.append(tokens_offsets_list)
            tokens = tokens_batch
        subword_tokens, subword_tok_ids, startofword_markers, subword_tags = [], [], [], []
        for i in range(len(tokens)):
            toks = tokens[i]
            ys = ["O"] * len(toks) if tags is None else tags[i]
            assert len(toks) == len(ys), f"toks({len(toks)}) should have the same length as ys({len(ys)})"
            sw_toks, sw_marker, sw_ys = self._ner_bert_tokenize(
                toks,
                ys,
                self.tokenizer,
                self.max_subword_length,
                mode=self.mode,
                subword_mask_mode=self.subword_mask_mode,
                token_masking_prob=self.token_masking_prob,
            )
            if self.max_seq_length is not None:
                if len(sw_toks) > self.max_seq_length:
                    raise RuntimeError(
                        f"input sequence after bert tokenization" f" shouldn't exceed {self.max_seq_length} tokens."
                    )
            subword_tokens.append(sw_toks)
            subword_tok_ids.append(self.tokenizer.convert_tokens_to_ids(sw_toks))
            startofword_markers.append(sw_marker)
            subword_tags.append(sw_ys)
            assert len(sw_marker) == len(sw_toks) == len(subword_tok_ids[-1]) == len(sw_ys), (
                f"length of sow_marker({len(sw_marker)}), tokens({len(sw_toks)}),"
                f" token ids({len(subword_tok_ids[-1])}) and ys({len(ys)})"
                f" for tokens = `{toks}` should match"
            )

        subword_tok_ids = zero_pad(subword_tok_ids, dtype=int, padding=0)
        startofword_markers = zero_pad(startofword_markers, dtype=int, padding=0)
        attention_mask = Mask()(subword_tokens)

        if tags is not None:
            if self.provide_subword_tags:
                return tokens, subword_tokens, subword_tok_ids, attention_mask, startofword_markers, subword_tags
            else:
                nonmasked_tags = [[t for t in ts if t != "X"] for ts in tags]
                for swts, swids, swms, ts in zip(subword_tokens, subword_tok_ids, startofword_markers, nonmasked_tags):
                    if (len(swids) != len(swms)) or (len(ts) != sum(swms)):
                        log.warning("Not matching lengths of the tokenization!")
                        log.warning(f"Tokens len: {len(swts)}\n Tokens: {swts}")
                        log.warning(f"Markers len: {len(swms)}, sum: {sum(swms)}")
                        log.warning(f"Masks: {swms}")
                        log.warning(f"Tags len: {len(ts)}\n Tags: {ts}")
                return tokens, subword_tokens, subword_tok_ids, attention_mask, startofword_markers, nonmasked_tags
        return tokens, subword_tokens, subword_tok_ids, startofword_markers, attention_mask, tokens_offsets_batch

    @staticmethod
    def _ner_bert_tokenize(
        tokens: List[str],
        tags: List[str],
        tokenizer: AutoTokenizer,
        max_subword_len: int = None,
        mode: str = None,
        subword_mask_mode: str = "first",
        token_masking_prob: float = None,
    ) -> Tuple[List[str], List[int], List[str]]:
        do_masking = (mode == "train") and (token_masking_prob is not None)
        do_cutting = max_subword_len is not None
        tokens_subword = ["[CLS]"]
        startofword_markers = [0]
        tags_subword = ["X"]
        for token, tag in zip(tokens, tags):
            token_marker = int(tag != "X")
            subwords = tokenizer.tokenize(token)
            if not subwords or (do_cutting and (len(subwords) > max_subword_len)):
                tokens_subword.append("[UNK]")
                startofword_markers.append(token_marker)
                tags_subword.append(tag)
            else:
                if do_masking and (random.random() < token_masking_prob):
                    tokens_subword.extend(["[MASK]"] * len(subwords))
                else:
                    tokens_subword.extend(subwords)
                if subword_mask_mode == "last":
                    startofword_markers.extend([0] * (len(subwords) - 1) + [token_marker])
                else:
                    startofword_markers.extend([token_marker] + [0] * (len(subwords) - 1))
                tags_subword.extend([tag] + ["X"] * (len(subwords) - 1))

        tokens_subword.append("[SEP]")
        startofword_markers.append(0)
        tags_subword.append("X")
        return tokens_subword, startofword_markers, tags_subword


@register("torch_transformers_el_tags_preprocessor")
class TorchTransformersElTagPreprocessor(Component):
    def __init__(
        self,
        vocab_file: str,
        do_lower_case: bool = False,
        max_seq_length: int = 512,
        max_subword_length: int = None,
        token_masking_prob: float = 0.0,
        return_offsets: bool = False,
        **kwargs,
    ):
        self._re_tokenizer = re.compile(r"[\w']+|[^\w ]")

        self.max_seq_length = max_seq_length
        self.max_subword_length = max_subword_length
        vocab_file = str(expand_path(vocab_file))
        self.tokenizer = AutoTokenizer.from_pretrained(vocab_file, do_lower_case=do_lower_case)
        self.token_masking_prob = token_masking_prob

    def __call__(self, tokens_batch, entity_offsets_batch, mentions_batch=None, pages_batch=None):
        token_ids_batch, attention_mask_batch, subw_tokens_batch, entity_subw_indices_batch = [], [], [], []
        if mentions_batch is None:
            mentions_batch = [[] for _ in tokens_batch]
        if pages_batch is None:
            pages_batch = [[] for _ in tokens_batch]

        for tokens, entity_offsets_list, mentions_list, pages_list in zip(
            tokens_batch, entity_offsets_batch, mentions_batch, pages_batch
        ):
            tokens_list = []
            tokens_offsets_list = []
            for elem in re.finditer(self._re_tokenizer, tokens):
                tokens_list.append(elem[0])
                tokens_offsets_list.append((elem.start(), elem.end()))

            entity_indices_list = []
            for start_offset, end_offset in entity_offsets_list:
                entity_indices = []
                for ind, (start_tok_offset, end_tok_offset) in enumerate(tokens_offsets_list):
                    if start_tok_offset >= start_offset and end_tok_offset <= end_offset:
                        entity_indices.append(ind)
                if not entity_indices:
                    for ind, (start_tok_offset, end_tok_offset) in enumerate(tokens_offsets_list):
                        if start_tok_offset >= start_offset:
                            entity_indices.append(ind)
                            break
                entity_indices_list.append(set(entity_indices))

            ind = 0
            subw_tokens_list = ["[CLS]"]
            entity_subw_indices_list = [[] for _ in entity_indices_list]
            for n, tok in enumerate(tokens_list):
                subw_tok = self.tokenizer.tokenize(tok)
                subw_tokens_list += subw_tok
                for j in range(len(entity_indices_list)):
                    if n in entity_indices_list[j]:
                        for k in range(len(subw_tok)):
                            entity_subw_indices_list[j].append(ind + k + 1)
                ind += len(subw_tok)
            subw_tokens_list.append("[SEP]")
            subw_tokens_batch.append(subw_tokens_list)

            for n in range(len(entity_subw_indices_list)):
                entity_subw_indices_list[n] = sorted(entity_subw_indices_list[n])
            entity_subw_indices_batch.append(entity_subw_indices_list)

        token_ids_batch = [
            self.tokenizer.convert_tokens_to_ids(subw_tokens_list) for subw_tokens_list in subw_tokens_batch
        ]
        token_ids_batch = zero_pad(token_ids_batch, dtype=int, padding=0)
        attention_mask_batch = Mask()(subw_tokens_batch)

        return token_ids_batch, attention_mask_batch, entity_subw_indices_batch


@register("torch_transformers_el_tags_postprocessor")
class TorchTransformersElTagPostprocessor(Component):
    def __init__(self, tags_file, **kwargs):
        tags_file = str(expand_path(tags_file))
        self.tags_list = []
        with open(tags_file, "r") as fl:
            lines = fl.readlines()
            for line in lines:
                self.tags_list.append(line.strip().split()[0])

    def __call__(self, entity_substr_batch, probas_batch):
        ent_tag_proba_batch = []
        for entity_substr_list, probas_list in zip(entity_substr_batch, probas_batch):
            ent_tag_proba_list = []
            if entity_substr_list:
                for probas in probas_list:
                    tags_with_probas = [(float(proba), self.tags_list[n]) for n, proba in enumerate(probas)]
                    tags_with_probas = sorted(tags_with_probas, key=lambda x: x[0], reverse=True)
                    ent_tag_proba_list.append(tags_with_probas[:3])
            ent_tag_proba_batch.append(ent_tag_proba_list)
        return ent_tag_proba_batch
