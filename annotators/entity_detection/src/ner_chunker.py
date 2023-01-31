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
import time
from pathlib import Path
from logging import getLogger
from string import punctuation
from typing import List, Tuple

import spacy
from deeppavlov.core.commands.utils import expand_path
from deeppavlov.core.common.chainer import Chainer
from deeppavlov.core.common.registry import register
from deeppavlov.core.models.component import Component
from nltk import sent_tokenize
from transformers import AutoTokenizer

from src.entity_detection_parser import EntityDetectionParser

log = getLogger(__name__)


@register("ner_chunker")
class NerChunker(Component):
    """
    Class to split documents into chunks of max_chunk_len symbols so that the length will not exceed
    maximal sequence length to feed into BERT
    """

    def __init__(
        self,
        vocab_file: str,
        max_seq_len: int = 400,
        max_chunk_len: int = 180,
        batch_size: int = 30,
        do_lower_case: bool = False,
        **kwargs,
    ):
        """

        Args:
            max_chunk_len: maximal length of chunks into which the document is split
            batch_size: how many chunks are in batch
        """
        self.max_seq_len = max_seq_len
        self.max_chunk_len = max_chunk_len
        self.batch_size = batch_size
        self.re_tokenizer = re.compile(r"[\w']+|[^\w ]")
        if Path(vocab_file).is_file():
            vocab_file = str(expand_path(vocab_file))
            self.tokenizer = AutoTokenizer(vocab_file=vocab_file, do_lower_case=do_lower_case)
        else:
            self.tokenizer = AutoTokenizer.from_pretrained(vocab_file, do_lower_case=do_lower_case)
        self.do_lower_case = do_lower_case
        self.punct_ext = punctuation + " " + "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        self.russian_letters = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"

    def __call__(self, docs_batch: List[str]) -> Tuple[List[List[str]], List[List[int]]]:
        """
        This method splits each document in the batch into chunks wuth the maximal length of max_chunk_len

        Args:
            docs_batch: batch of documents

        Returns:
            batch of lists of document chunks for each document
            batch of lists of numbers of documents which correspond to chunks
        """
        text_batch_list = []
        text_batch = []
        nums_batch_list = []
        nums_batch = []
        sentences_offsets_batch_list = []
        sentences_offsets_batch = []
        sentences_batch_list = []
        sentences_batch = []

        for n, doc in enumerate(docs_batch):
            if self.do_lower_case:
                doc = doc.lower()
            start = 0
            text = ""
            sentences_list = []
            sentences_offsets_list = []
            cur_len = 0
            doc_pieces = doc.split("\n")
            doc_pieces = [self.sanitize(doc_piece) for doc_piece in doc_pieces]
            doc_pieces = [doc_piece for doc_piece in doc_pieces if len(doc_piece) > 1]
            sentences = []
            for doc_piece in doc_pieces:
                sentences += sent_tokenize(doc_piece)
            for sentence in sentences:
                sentence_tokens = re.findall(self.re_tokenizer, sentence)
                sentence_len = sum([len(self.tokenizer.tokenize(token)) for token in sentence_tokens])
                if cur_len + sentence_len < self.max_seq_len:
                    text += f"{sentence} "
                    cur_len += sentence_len
                    end = start + len(sentence)
                    sentences_offsets_list.append((start, end))
                    sentences_list.append(sentence)
                    start = end + 1
                else:
                    text = text.strip()
                    if text:
                        text_batch.append(text)
                        sentences_offsets_batch.append(sentences_offsets_list)
                        sentences_batch.append(sentences_list)
                        nums_batch.append(n)

                    if sentence_len < self.max_seq_len:
                        text = f"{sentence} "
                        cur_len = sentence_len
                        start = 0
                        end = start + len(sentence)
                        sentences_offsets_list = [(start, end)]
                        sentences_list = [sentence]
                        start = end + 1
                    else:
                        text = ""
                        if "," in sentence:
                            sentence_chunks = sentence.split(", ")
                            for chunk in sentence_chunks:
                                chunk_tokens = re.findall(self.re_tokenizer, chunk)
                                chunk_len = sum([len(self.tokenizer.tokenize(token)) for token in chunk_tokens])
                                if cur_len + chunk_len < self.max_seq_len:
                                    text += f"{chunk}, "
                                    cur_len += chunk_len + 1
                                    end = start + len(chunk) + 1
                                    sentences_offsets_list.append((start, end))
                                    sentences_list.append(chunk)
                                    start = end + 1
                                else:
                                    text = text.strip().strip(",")
                                    if text:
                                        text_batch.append(text)
                                        sentences_offsets_batch.append(sentences_offsets_list)
                                        sentences_batch.append(sentences_list)
                                        nums_batch.append(n)

                                    chunk = " ".join(chunk.split()[: self.max_chunk_len])
                                    text = f"{chunk}, "
                                    cur_len = chunk_len
                                    start = 0
                                    end = start + len(chunk)
                                    sentences_offsets_list = [(start, end)]
                                    sentences_list = [sentence]
                                    start = end + 1
                        else:
                            chunk_tokens = sentence.split()
                            num_chunks = len(chunk_tokens) // self.max_chunk_len + int(
                                len(chunk_tokens) % self.max_chunk > 0
                            )
                            for ii in range(num_chunks):
                                chunk_tokens_elem = chunk_tokens[
                                    ii * self.max_chunk_len : (ii + 1) * self.max_chunk_len
                                ]
                                text_batch.append(" ".join(chunk_tokens_elem))
                                sentences_offsets_batch.append([(0, len(chunk_tokens_elem))])
                                sentences_batch.append([chunk_tokens_elem])
                                nums_batch.append(n)

            text = text.strip().strip(",")
            if text:
                text_batch.append(text)
                nums_batch.append(n)
                sentences_offsets_batch.append(sentences_offsets_list)
                sentences_batch.append(sentences_list)

        num_batches = len(text_batch) // self.batch_size + int(len(text_batch) % self.batch_size > 0)
        for jj in range(num_batches):
            text_batch_list.append(text_batch[jj * self.batch_size : (jj + 1) * self.batch_size])
            nums_batch_list.append(nums_batch[jj * self.batch_size : (jj + 1) * self.batch_size])
            sentences_offsets_batch_list.append(
                sentences_offsets_batch[jj * self.batch_size : (jj + 1) * self.batch_size]
            )
            sentences_batch_list.append(sentences_batch[jj * self.batch_size : (jj + 1) * self.batch_size])

        return text_batch_list, nums_batch_list, sentences_offsets_batch_list, sentences_batch_list

    def sanitize(self, text):
        text_len = len(text)

        if text_len > 0 and text[text_len - 1] not in {".", "!", "?"}:
            i = text_len - 1
            while text[i] in self.punct_ext and i > 0:
                i -= 1
                if (text[i] in {".", "!", "?"} and text[i - 1].lower() in self.russian_letters) or (
                    i > 1
                    and text[i] in {".", "!", "?"}
                    and text[i - 1] in '"'
                    and text[i - 2].lower() in self.russian_letters
                ):
                    break

            text = text[: i + 1]
        text = re.sub(r"\s+", " ", text)
        return text


@register("ner_chunk_model")
class NerChunkModel(Component):
    """
    Class for linking of entity substrings in the document to entities in Wikidata
    """

    def __init__(self, ner: Chainer, ner_parser: EntityDetectionParser, add_nouns: False, **kwargs) -> None:
        """

        Args:
            ner: config for entity detection
            ner_parser: component deeppavlov.models.kbqa.entity_detection_parser
            **kwargs:
        """
        self.ner = ner
        self.ner_parser = ner_parser
        self.re_tokenizer = re.compile(r"[\w']+|[^\w ]")
        self.add_nouns = add_nouns
        self.nlp = spacy.load("en_core_web_sm")

    def __call__(
        self,
        text_batch_list: List[List[str]],
        nums_batch_list: List[List[int]],
        sentences_offsets_batch_list: List[List[List[Tuple[int, int]]]],
        sentences_batch_list: List[List[List[str]]],
    ):
        entity_substr_batch_list = []
        entity_offsets_batch_list = []
        tags_batch_list = []
        entity_probas_batch_list = []
        tokens_conf_batch_list = []
        text_len_batch_list = []
        ner_tokens_batch_list = []
        entity_positions_batch_list = []
        sentences_tokens_batch_list = []
        for text_batch, sentences_offsets_batch, sentences_batch in zip(
            text_batch_list, sentences_offsets_batch_list, sentences_batch_list
        ):
            tm_ner_st = time.time()
            ner_tokens_batch, ner_tokens_offsets_batch, ner_probas_batch, probas_batch = self.ner(text_batch)
            log.debug(
                f"ner_tokens_batch {ner_tokens_batch} ner_tokens_offsets_batch {ner_tokens_offsets_batch} "
                f"ner_probas_batch {ner_probas_batch} probas_batch {probas_batch}"
            )
            if self.add_nouns:
                for i in range(len(ner_tokens_batch)):
                    cur_text = text_batch[i]
                    doc = list(self.nlp(cur_text))
                    k = 0
                    for j in range(len(ner_tokens_batch[i])):
                        found = False
                        if k < len(doc) and ner_tokens_batch[i][j] == doc[k].text:
                            if doc[k].pos_ == "NOUN":
                                found = True
                            k += 1
                        elif k < len(doc) - 1 and ner_tokens_batch[i][j] == doc[k + 1].text:
                            if doc[k + 1].pos_ == "NOUN":
                                found = True
                            k += 2
                        elif k < len(doc) - 2 and ner_tokens_batch[i][j] == doc[k + 2].text:
                            if doc[k + 2].pos_ == "NOUN":
                                found = True
                            k += 3
                        if found and ner_probas_batch[i][j] == "O":
                            ner_probas_batch[i][j] = "B-MISC"

            entity_substr_batch, entity_positions_batch, entity_probas_batch, tokens_conf_batch = self.ner_parser(
                text_batch, ner_tokens_batch, ner_probas_batch, probas_batch
            )
            tm_ner_end = time.time()
            log.debug(f"ner time {tm_ner_end - tm_ner_st}")
            log.debug(
                f"entity_substr_batch {entity_substr_batch} entity_positions_batch {entity_positions_batch} "
                f"entity_probas_batch {entity_probas_batch} tokens_conf_batch {tokens_conf_batch}"
            )
            entity_pos_tags_probas_batch = [
                [
                    (entity_substr.lower(), entity_substr_positions, tag, entity_proba)
                    for tag, entity_substr_list in entity_substr_dict.items()
                    for entity_substr, entity_substr_positions, entity_proba in zip(
                        entity_substr_list, entity_positions_dict[tag], entity_probas_dict[tag]
                    )
                ]
                for entity_substr_dict, entity_positions_dict, entity_probas_dict in zip(
                    entity_substr_batch, entity_positions_batch, entity_probas_batch
                )
            ]
            entity_substr_batch = []
            entity_offsets_batch = []
            tags_batch = []
            probas_batch = []
            pr_entity_positions_batch = []
            for entity_pos_tags_probas, ner_tokens_offsets_list in zip(
                entity_pos_tags_probas_batch, ner_tokens_offsets_batch
            ):
                if entity_pos_tags_probas:
                    entity_offsets_list = []
                    entity_substr_list, entity_positions_list, tags_list, probas_list = zip(*entity_pos_tags_probas)
                    for entity_positions in entity_positions_list:
                        start_offset = ner_tokens_offsets_list[entity_positions[0]][0]
                        end_offset = ner_tokens_offsets_list[entity_positions[-1]][1]
                        entity_offsets_list.append((start_offset, end_offset))
                else:
                    entity_substr_list, entity_offsets_list, tags_list, probas_list, entity_positions_list = (
                        [],
                        [],
                        [],
                        [],
                        [],
                    )
                entity_substr_batch.append(list(entity_substr_list))
                entity_offsets_batch.append(list(entity_offsets_list))
                tags_batch.append(list(tags_list))
                probas_batch.append(list(probas_list))
                pr_entity_positions_batch.append(list(entity_positions_list))

            sentences_tokens_batch = []
            for sentences_offsets_list, ner_tokens_list, ner_tokens_offsets_list in zip(
                sentences_offsets_batch, ner_tokens_batch, ner_tokens_offsets_batch
            ):
                sentences_tokens_list = []
                for start_offset, end_offset in sentences_offsets_list:
                    sentence_tokens = []
                    for tok, (start_tok_offset, end_tok_offset) in zip(ner_tokens_list, ner_tokens_offsets_list):
                        if start_tok_offset >= start_offset and end_tok_offset <= end_offset:
                            sentence_tokens.append(tok)
                    sentences_tokens_list.append(sentence_tokens)
                sentences_tokens_batch.append(sentences_tokens_list)

            log.debug(f"entity_substr_batch {entity_substr_batch}")
            log.debug(f"entity_offsets_batch {entity_offsets_batch}")

            entity_substr_batch_list.append(entity_substr_batch)
            tags_batch_list.append(tags_batch)
            entity_offsets_batch_list.append(entity_offsets_batch)
            entity_probas_batch_list.append(probas_batch)
            text_len_batch_list.append([len(text) for text in text_batch])
            ner_tokens_batch_list.append(ner_tokens_batch)
            tokens_conf_batch_list.append(tokens_conf_batch)
            entity_positions_batch_list.append(pr_entity_positions_batch)
            sentences_tokens_batch_list.append(sentences_tokens_batch)

        doc_entity_substr_batch, doc_tags_batch, doc_entity_offsets_batch, doc_probas_batch = [], [], [], []
        doc_sentences_offsets_batch, doc_sentences_batch = [], []
        doc_ner_tokens_batch, doc_tokens_conf_batch, doc_entity_positions_batch, doc_sentences_tokens_batch = (
            [],
            [],
            [],
            [],
        )
        doc_entity_substr, doc_tags, doc_probas, doc_entity_offsets = [], [], [], []
        doc_sentences_offsets, doc_sentences = [], []
        doc_ner_tokens, doc_tokens_conf, doc_entity_positions, doc_sentences_tokens = [], [], [], []
        cur_doc_num = 0
        text_len_sum = 0
        tokens_len_sum = 0
        for (
            entity_substr_batch,
            tags_batch,
            probas_batch,
            entity_offsets_batch,
            sentences_offsets_batch,
            sentences_batch,
            text_len_batch,
            nums_batch,
            ner_tokens_batch,
            tokens_conf_batch,
            entity_positions_batch,
            sentences_tokens_batch,
        ) in zip(
            entity_substr_batch_list,
            tags_batch_list,
            entity_probas_batch_list,
            entity_offsets_batch_list,
            sentences_offsets_batch_list,
            sentences_batch_list,
            text_len_batch_list,
            nums_batch_list,
            ner_tokens_batch_list,
            tokens_conf_batch_list,
            entity_positions_batch_list,
            sentences_tokens_batch_list,
        ):
            for (
                entity_substr,
                tag,
                probas,
                entity_offsets,
                sentences_offsets,
                sentences,
                text_len,
                doc_num,
                ner_tokens,
                tokens_conf,
                entity_positions,
                sentences_tokens,
            ) in zip(
                entity_substr_batch,
                tags_batch,
                probas_batch,
                entity_offsets_batch,
                sentences_offsets_batch,
                sentences_batch,
                text_len_batch,
                nums_batch,
                ner_tokens_batch,
                tokens_conf_batch,
                entity_positions_batch,
                sentences_tokens_batch,
            ):
                if doc_num == cur_doc_num:
                    doc_entity_substr += entity_substr
                    doc_tags += tag
                    doc_probas += probas
                    doc_entity_offsets += [
                        (start_offset + text_len_sum, end_offset + text_len_sum)
                        for start_offset, end_offset in entity_offsets
                    ]
                    doc_sentences_offsets += [
                        (start_offset + text_len_sum, end_offset + text_len_sum)
                        for start_offset, end_offset in sentences_offsets
                    ]
                    doc_entity_positions += [
                        [pos + tokens_len_sum for pos in entity_position] for entity_position in entity_positions
                    ]
                    doc_sentences += sentences
                    text_len_sum += text_len + 1
                    doc_ner_tokens += ner_tokens
                    doc_tokens_conf += tokens_conf
                    tokens_len_sum += len(ner_tokens)
                    doc_sentences_tokens += sentences_tokens
                else:
                    doc_entity_substr_batch.append(doc_entity_substr)
                    doc_tags_batch.append(doc_tags)
                    doc_probas_batch.append(doc_probas)
                    doc_entity_offsets_batch.append(doc_entity_offsets)
                    doc_sentences_offsets_batch.append(doc_sentences_offsets)
                    doc_entity_positions_batch.append(doc_entity_positions)
                    doc_sentences_batch.append(doc_sentences)
                    doc_ner_tokens_batch.append(doc_ner_tokens)
                    doc_tokens_conf_batch.append(doc_tokens_conf)
                    doc_sentences_tokens_batch.append(doc_sentences_tokens)
                    doc_entity_substr = entity_substr
                    doc_tags = tag
                    doc_probas = probas
                    doc_entity_offsets = entity_offsets
                    doc_sentences_offsets = sentences_offsets
                    doc_entity_positions = entity_positions
                    doc_sentences = sentences
                    cur_doc_num = doc_num
                    text_len_sum = text_len
                    doc_ner_tokens = ner_tokens
                    doc_tokens_conf = tokens_conf
                    doc_sentences_tokens = sentences_tokens
                    tokens_len_sum = len(ner_tokens)
        doc_entity_substr_batch.append(doc_entity_substr)
        doc_tags_batch.append(doc_tags)
        doc_probas_batch.append(doc_probas)
        doc_entity_offsets_batch.append(doc_entity_offsets)
        doc_sentences_offsets_batch.append(doc_sentences_offsets)
        doc_entity_positions_batch.append(doc_entity_positions)
        doc_sentences_batch.append(doc_sentences)
        doc_ner_tokens_batch.append(doc_ner_tokens)
        doc_tokens_conf_batch.append(doc_tokens_conf)
        doc_sentences_tokens_batch.append(doc_sentences_tokens)

        return (
            doc_entity_substr_batch,
            doc_entity_offsets_batch,
            doc_tags_batch,
            doc_probas_batch,
            doc_sentences_offsets_batch,
            doc_sentences_batch,
            doc_ner_tokens_batch,
            doc_tokens_conf_batch,
            doc_entity_positions_batch,
            doc_sentences_tokens_batch,
        )
