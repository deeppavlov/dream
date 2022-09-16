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
import sqlite3
from logging import getLogger
from typing import List, Dict, Tuple
from collections import defaultdict

import nltk
from nltk.corpus import stopwords
from rapidfuzz import fuzz

from deeppavlov.core.common.registry import register
from deeppavlov.core.models.component import Component
from deeppavlov.core.models.serializable import Serializable
from deeppavlov.core.commands.utils import expand_path
from src.find_word import WordSearcher

log = getLogger(__name__)
nltk.download("stopwords")


@register("entity_linker")
class EntityLinker(Component, Serializable):
    """
    Class for linking of entity substrings in the document to entities in Wikidata
    """

    def __init__(
        self,
        load_path: str,
        tags_filename: str,
        add_info_filename: str,
        words_dict_filename: str = None,
        ngrams_matrix_filename: str = None,
        entity_ranker=None,
        num_entities_for_bert_ranking: int = 50,
        num_entities_to_return: int = 10,
        max_text_len: int = 300,
        max_paragraph_len: int = 150,
        lang: str = "ru",
        use_descriptions: bool = True,
        use_tags: bool = False,
        lemmatize: bool = False,
        full_paragraph: bool = False,
        use_connections: bool = False,
        **kwargs,
    ) -> None:
        """

        Args:
            load_path: path to folder with inverted index files
            entity_ranker: component deeppavlov.models.kbqa.rel_ranking_bert
            num_entities_for_bert_ranking: number of candidate entities for BERT ranking using description and context
            ngram_range: char ngrams range for TfidfVectorizer
            num_entities_to_return: number of candidate entities for the substring which are returned
            lang: russian or english
            use_description: whether to perform entity ranking by context and description
            lemmatize: whether to lemmatize tokens
            **kwargs:
        """
        super().__init__(save_path=None, load_path=load_path)
        self.lemmatize = lemmatize
        self.tags_filename = tags_filename
        self.add_info_filename = add_info_filename
        self.words_dict_filename = words_dict_filename
        self.ngrams_matrix_filename = ngrams_matrix_filename
        self.num_entities_for_bert_ranking = num_entities_for_bert_ranking
        self.entity_ranker = entity_ranker
        self.num_entities_to_return = num_entities_to_return
        self.max_text_len = max_text_len
        self.max_paragraph_len = max_paragraph_len
        self.lang = f"@{lang}"
        if self.lang == "@en":
            self.stopwords = set(stopwords.words("english"))
        elif self.lang == "@ru":
            self.stopwords = set(stopwords.words("russian"))
        self.use_descriptions = use_descriptions
        self.use_connections = use_connections
        self.use_tags = use_tags
        self.full_paragraph = full_paragraph
        self.re_tokenizer = re.compile(r"[\w']+|[^\w ]")
        self.not_found_str = "not in wiki"
        self.related_tags = {
            "loc": ["gpe", "country", "city", "us_state", "river"],
            "gpe": ["loc", "country", "city", "us_state"],
            "work_of_art": ["product", "law"],
            "product": ["work_of_art"],
            "law": ["work_of_art"],
            "org": ["fac", "business"],
            "business": ["org"],
            "actor": ["per"],
            "athlete": ["per"],
            "musician": ["per"],
            "politician": ["per"],
            "writer": ["per"],
        }
        self.word_searcher = None
        if self.words_dict_filename:
            self.word_searcher = WordSearcher(self.words_dict_filename, self.ngrams_matrix_filename)
        self.load()

    def load(self) -> None:
        with open(str(expand_path(self.tags_filename)), "r") as fl:
            lines = fl.readlines()
        tags = []
        for line in lines:
            tag_str = line.strip().split()[:-1]
            tags.append("_".join(tag_str))
        if "O" in tags:
            tags.remove("O")
        self.cursors = {}
        for tag in tags:
            conn = sqlite3.connect(f"{self.load_path}/{tag.lower()}.db", check_same_thread=False)
            cur = conn.cursor()
            self.cursors[tag.lower()] = cur
        conn = sqlite3.connect(str(expand_path(self.add_info_filename)), check_same_thread=False)
        self.add_info_cur = conn.cursor()

    def save(self) -> None:
        pass

    def __call__(
        self,
        entity_substr_batch: List[List[str]],
        entity_tags_batch: List[List[str]] = None,
        sentences_batch: List[List[str]] = None,
        entity_offsets_batch: List[List[List[int]]] = None,
        sentences_offsets_batch: List[List[Tuple[int, int]]] = None,
    ):
        if sentences_offsets_batch is None and sentences_batch is not None:
            sentences_offsets_batch = []
            for sentences_list in sentences_batch:
                sentences_offsets_list = []
                start = 0
                for sentence in sentences_list:
                    end = start + len(sentence)
                    sentences_offsets_list.append([start, end])
                    start = end + 1
                sentences_offsets_batch.append(sentences_offsets_list)

        if sentences_batch is None:
            sentences_batch = [[] for _ in entity_substr_batch]
            sentences_offsets_batch = [[] for _ in entity_substr_batch]

        log.info(f"sentences_batch {sentences_batch}")
        if entity_offsets_batch is None and sentences_batch is not None:
            entity_offsets_batch = []
            for entity_substr_list, sentences_list in zip(entity_substr_batch, sentences_batch):
                text = " ".join(sentences_list).lower()
                log.info(f"text {text}")
                entity_offsets_list = []
                for entity_substr in entity_substr_list:
                    st_offset = text.find(entity_substr.lower())
                    end_offset = st_offset + len(entity_substr)
                    entity_offsets_list.append([st_offset, end_offset])
                entity_offsets_batch.append(entity_offsets_list)

        entity_ids_batch, entity_conf_batch, entity_pages_batch = [], [], []
        for entity_substr_list, entity_offsets_list, entity_tags_list, sentences_list, sentences_offsets_list in zip(
            entity_substr_batch, entity_offsets_batch, entity_tags_batch, sentences_batch, sentences_offsets_batch
        ):
            entity_ids_list, entity_conf_list, entity_pages_list = self.link_entities(
                entity_substr_list,
                entity_offsets_list,
                entity_tags_list,
                sentences_list,
                sentences_offsets_list,
            )
            log.info(f"entity_ids_list {entity_ids_list} entity_conf_list {entity_conf_list}")
            if self.num_entities_to_return == 1:
                entity_pages_list = [entity_pages[0] for entity_pages in entity_pages_list]
            else:
                entity_pages_list = [entity_pages[: self.num_entities_to_return] for entity_pages in entity_pages_list]
            entity_ids_batch.append(entity_ids_list)
            entity_conf_batch.append(entity_conf_list)
            entity_pages_batch.append(entity_pages_list)
            first_par_batch, dbpedia_types_batch = self.extract_add_info(entity_pages_batch)
        return entity_ids_batch, entity_conf_batch, entity_pages_batch, first_par_batch, dbpedia_types_batch

    def extract_add_info(self, entity_pages_batch: List[List[List[str]]]):
        first_par_batch, dbpedia_types_batch = [], []
        for entity_pages_list in entity_pages_batch:
            first_par_list, dbpedia_types_list = [], []
            for entity_pages in entity_pages_list:
                first_pars, dbpedia_types = [], []
                for entity_page in entity_pages:
                    try:
                        query = "SELECT * FROM entity_additional_info WHERE page_title='{}';".format(entity_page)
                        res = self.add_info_cur.execute(query)
                        fetch_res = res.fetchall()
                        first_par = fetch_res[0][1]
                        dbpedia_types_elem = fetch_res[0][2].split()
                        first_pars.append(first_par)
                        dbpedia_types.append(dbpedia_types_elem)
                    except Exception as e:
                        first_pars.append("")
                        dbpedia_types.append([])
                        log.info(f"error {e}")
                first_par_list.append(first_pars)
                dbpedia_types_list.append(dbpedia_types)
            first_par_batch.append(first_par_list)
            dbpedia_types_batch.append(dbpedia_types_list)
        return first_par_batch, dbpedia_types_batch

    def link_entities(
        self,
        entity_substr_list: List[str],
        entity_offsets_list: List[List[int]],
        entity_tags_list: List[str],
        sentences_list: List[str],
        sentences_offsets_list: List[List[int]],
    ) -> List[List[str]]:
        log.info(
            f"entity_substr_list {entity_substr_list} entity_tags_list {entity_tags_list} "
            f"entity_offsets_list {entity_offsets_list}"
        )
        entity_ids_list, conf_list, pages_list, pages_dict_list, descr_list = [], [], [], [], []
        if entity_substr_list:
            entities_scores_list = []
            cand_ent_scores_list = []
            for entity_substr, tags in zip(entity_substr_list, entity_tags_list):
                for symb_old, symb_new in [("'", "''"), ("-", " "), ("@", ""), (".", ""), ("  ", " ")]:
                    entity_substr = entity_substr.replace(symb_old, symb_new)
                cand_ent_init = defaultdict(set)
                if len(entity_substr) > 1:
                    cand_ent_init = self.find_exact_match(entity_substr, tags)
                    all_low_conf = True
                    for entity_id in cand_ent_init:
                        entity_info_set = cand_ent_init[entity_id]
                        for entity_info in entity_info_set:
                            if entity_info[0] == 1.0:
                                all_low_conf = False
                                break
                        if not all_low_conf:
                            break
                    clean_tags = [tag for tag, conf in tags]
                    corr_tags, corr_clean_tags = [], []
                    for tag, conf in tags:
                        if tag in self.related_tags:
                            corr_tag_list = self.related_tags[tag]
                            for corr_tag in corr_tag_list:
                                if corr_tag not in clean_tags and corr_tag not in corr_clean_tags:
                                    corr_tags.append([corr_tag, conf])
                                    corr_clean_tags.append(corr_tag)

                    if (not cand_ent_init or all_low_conf) and corr_tags:
                        corr_cand_ent_init = self.find_exact_match(entity_substr, corr_tags)
                        cand_ent_init = {**cand_ent_init, **corr_cand_ent_init}
                    entity_substr_split = [
                        word for word in entity_substr.split(" ") if word not in self.stopwords and len(word) > 0
                    ]
                    if (
                        not cand_ent_init
                        and len(entity_substr_split) == 1
                        and self.word_searcher
                        and all([letter.isalpha() for letter in entity_substr_split[0]])
                    ):
                        corr_words = self.word_searcher(entity_substr_split[0], set(clean_tags + corr_clean_tags))
                        if corr_words:
                            cand_ent_init = self.find_exact_match(corr_words[0], tags + corr_tags)
                    if not cand_ent_init and len(entity_substr_split) > 1:
                        cand_ent_init = self.find_fuzzy_match(entity_substr_split, tags)

                cand_ent_scores = []
                for entity in cand_ent_init:
                    entities_scores = list(cand_ent_init[entity])
                    entities_scores = sorted(entities_scores, key=lambda x: (x[0], x[3], x[2]), reverse=True)
                    cand_ent_scores.append(([entity] + list(entities_scores[0])))

                cand_ent_scores = sorted(cand_ent_scores, key=lambda x: (x[1], x[4], x[3]), reverse=True)
                cand_ent_scores = cand_ent_scores[: self.num_entities_for_bert_ranking]
                cand_ent_scores_list.append(cand_ent_scores)
                entity_ids = [elem[0] for elem in cand_ent_scores]
                pages = [elem[5] for elem in cand_ent_scores]
                scores = [elem[1:5] for elem in cand_ent_scores]
                entities_scores_list.append(
                    {entity_id: entity_scores for entity_id, entity_scores in zip(entity_ids, scores)}
                )
                entity_ids_list.append(entity_ids)
                pages_list.append(pages)
                pages_dict_list.append({entity_id: page for entity_id, page in zip(entity_ids, pages)})
                descr_list.append([elem[6] for elem in cand_ent_scores])

            if self.use_descriptions:
                substr_lens = [len(entity_substr.split()) for entity_substr in entity_substr_list]
                entity_ids_list, conf_list = self.rank_by_description(
                    entity_substr_list,
                    entity_tags_list,
                    entity_offsets_list,
                    entity_ids_list,
                    descr_list,
                    entities_scores_list,
                    sentences_list,
                    sentences_offsets_list,
                    substr_lens,
                )
                pages_list = [
                    [pages_dict.get(entity_id, "") for entity_id in entity_ids]
                    for entity_ids, pages_dict in zip(entity_ids_list, pages_dict_list)
                ]

        return entity_ids_list, conf_list, pages_list

    def process_cand_ent(self, cand_ent_init, entities_and_ids, entity_substr_split, tag, tag_conf):
        for entity_title, entity_id, entity_rels, anchor_cnt, _, page, descr in entities_and_ids:
            substr_score = self.calc_substr_score(entity_title, entity_substr_split)
            cand_ent_init[entity_id].add((substr_score, anchor_cnt, entity_rels, tag_conf, page, descr))
        return cand_ent_init

    def find_exact_match(self, entity_substr, tags):
        entity_substr = entity_substr.lower()
        entity_substr_split = entity_substr.split()
        cand_ent_init = defaultdict(set)
        for tag, tag_conf in tags:
            if tag.lower() in self.cursors:
                query = "SELECT * FROM inverted_index WHERE title MATCH '{}';".format(entity_substr)
                res = self.cursors[tag.lower()].execute(query)
                entities_and_ids = res.fetchall()
                if entities_and_ids:
                    cand_ent_init = self.process_cand_ent(
                        cand_ent_init, entities_and_ids, entity_substr_split, tag, tag_conf
                    )
        if tags and tags[0][0] == "misc" and not cand_ent_init:
            for tag in self.cursors:
                query = "SELECT * FROM inverted_index WHERE title MATCH '{}';".format(entity_substr)
                res = self.cursors[tag].execute(query)
                entities_and_ids = res.fetchall()
                if entities_and_ids:
                    cand_ent_init = self.process_cand_ent(
                        cand_ent_init, entities_and_ids, entity_substr_split, tag, tag_conf
                    )
        return cand_ent_init

    def find_fuzzy_match(self, entity_substr_split, tags):
        entity_substr_split = [word.lower() for word in entity_substr_split]
        cand_ent_init = defaultdict(set)
        for tag, tag_conf in tags:
            if tag.lower() in self.cursors:
                for word in entity_substr_split:
                    query = "SELECT * FROM inverted_index WHERE title MATCH '{}';".format(word)
                    res = self.cursors[tag.lower()].execute(query)
                    part_entities_and_ids = res.fetchall()
                    cand_ent_init = self.process_cand_ent(
                        cand_ent_init, part_entities_and_ids, entity_substr_split, tag, tag_conf
                    )
        return cand_ent_init

    def calc_substr_score(self, entity_title, entity_substr_split):
        label_tokens = entity_title.split()
        cnt = 0.0
        for ent_tok in entity_substr_split:
            found = False
            for label_tok in label_tokens:
                if label_tok == ent_tok:
                    found = True
                    break
            if found:
                cnt += 1.0
            else:
                for label_tok in label_tokens:
                    if label_tok[:2] == ent_tok[:2]:
                        fuzz_score = fuzz.ratio(label_tok, ent_tok)
                        if fuzz_score >= 80.0 and not found:
                            cnt += fuzz_score * 0.01
                            break
        substr_score = round(cnt / max(len(label_tokens), len(entity_substr_split)), 3)
        if len(label_tokens) == 2 and len(entity_substr_split) == 1:
            if entity_substr_split[0] == label_tokens[1]:
                substr_score = 0.5
            elif entity_substr_split[0] == label_tokens[0]:
                substr_score = 0.3
        return substr_score

    def rank_by_description(
        self,
        entity_substr_list: List[str],
        entity_tags_list: List[List[Tuple[str, int]]],
        entity_offsets_list: List[List[int]],
        cand_ent_list: List[List[str]],
        cand_ent_descr_list: List[List[str]],
        entities_scores_list: List[Dict[str, Tuple[int, float]]],
        sentences_list: List[str],
        sentences_offsets_list: List[Tuple[int, int]],
        substr_lens: List[int],
    ) -> List[List[str]]:
        entity_ids_list = []
        conf_list = []
        contexts = []
        for entity_start_offset, entity_end_offset in entity_offsets_list:
            sentence = ""
            rel_start_offset = 0
            rel_end_offset = 0
            found_sentence_num = 0
            for num, (sent, (sent_start_offset, sent_end_offset)) in enumerate(
                zip(sentences_list, sentences_offsets_list)
            ):
                if entity_start_offset >= sent_start_offset and entity_end_offset <= sent_end_offset:
                    sentence = sent
                    found_sentence_num = num
                    rel_start_offset = entity_start_offset - sent_start_offset
                    rel_end_offset = entity_end_offset - sent_start_offset
                    break
            context = ""
            if sentence:
                start_of_sentence = 0
                end_of_sentence = len(sentence)
                if len(sentence) > self.max_text_len:
                    start_of_sentence = max(rel_start_offset - self.max_text_len // 2, 0)
                    end_of_sentence = min(rel_end_offset + self.max_text_len // 2, len(sentence))
                text_before = sentence[start_of_sentence:rel_start_offset]
                text_after = sentence[rel_end_offset:end_of_sentence]
                context = text_before + "[ent]" + text_after
                if self.full_paragraph:
                    cur_sent_len = len(re.findall(self.re_tokenizer, context))
                    first_sentence_num = found_sentence_num
                    last_sentence_num = found_sentence_num
                    context = [context]
                    while True:
                        added = False
                        if last_sentence_num < len(sentences_list) - 1:
                            sentence_tokens = re.findall(self.re_tokenizer, sentences_list[last_sentence_num + 1])
                            last_sentence_len = len(sentence_tokens)
                            if cur_sent_len + last_sentence_len < self.max_paragraph_len:
                                context.append(sentences_list[last_sentence_num + 1])
                                cur_sent_len += last_sentence_len
                                last_sentence_num += 1
                                added = True
                        if first_sentence_num > 0:
                            sentence_tokens = re.findall(self.re_tokenizer, sentences_list[first_sentence_num - 1])
                            first_sentence_len = len(sentence_tokens)
                            if cur_sent_len + first_sentence_len < self.max_paragraph_len:
                                context = [sentences_list[first_sentence_num - 1]] + context
                                cur_sent_len += first_sentence_len
                                first_sentence_num -= 1
                                added = True
                        if not added:
                            break
                    context = " ".join(context)

            log.info(f"rank, context: {context}")
            contexts.append(context)

        scores_list = self.entity_ranker(contexts, cand_ent_list, cand_ent_descr_list)

        for context, entity_tags, candidate_entities, substr_len, entities_scores, scores in zip(
            contexts, entity_tags_list, cand_ent_list, substr_lens, entities_scores_list, scores_list
        ):
            log.info(f"len candidate entities {len(candidate_entities)}")
            if len(context.split()) < 4:
                entities_with_scores = [
                    (
                        entity,
                        round(entities_scores.get(entity, (0.0, 0, 0))[0], 2),
                        entities_scores.get(entity, (0.0, 0, 0))[1],
                        entities_scores.get(entity, (0.0, 0, 0))[2],
                        0.95,
                    )
                    for entity, score in scores
                ]
            else:
                entities_with_scores = [
                    (
                        entity,
                        round(entities_scores.get(entity, (0.0, 0, 0))[0], 2),
                        entities_scores.get(entity, (0.0, 0, 0))[1],
                        entities_scores.get(entity, (0.0, 0, 0))[2],
                        round(score, 2),
                    )
                    for entity, score in scores
                ]
            log.info(f"len entities with scores {len(entities_with_scores)}")
            if entity_tags and entity_tags[0][0] == "misc":
                entities_with_scores = sorted(entities_with_scores, key=lambda x: (x[1], x[2], x[4]), reverse=True)
            else:
                entities_with_scores = sorted(entities_with_scores, key=lambda x: (x[1], x[4], x[3]), reverse=True)
            log.info(f"--- entities_with_scores {entities_with_scores}")

            if not entities_with_scores:
                top_entities = [self.not_found_str]
                top_conf = [(0.0, 0, 0, 0.0)]
            elif entities_with_scores and substr_len == 1 and entities_with_scores[0][1] < 1.0:
                top_entities = [self.not_found_str]
                top_conf = [(0.0, 0, 0, 0.0)]
            elif entities_with_scores and (
                entities_with_scores[0][1] < 0.3
                or (entities_with_scores[0][4] < 0.13 and entities_with_scores[0][3] < 20)
                or (entities_with_scores[0][4] < 0.3 and entities_with_scores[0][3] < 4)
                or entities_with_scores[0][1] < 0.6
            ):
                top_entities = [self.not_found_str]
                top_conf = [(0.0, 0, 0, 0.0)]
            else:
                top_entities = [score[0] for score in entities_with_scores]
                top_conf = [score[1:] for score in entities_with_scores]

            log.info(f"--- top_entities {top_entities} top_conf {top_conf}")

            high_conf_entities = []
            high_conf_nums = []
            for elem_num, (entity, conf) in enumerate(zip(top_entities, top_conf)):
                if len(conf) == 3 and conf[0] == 1.0 and conf[2] > 50 and conf[3] > 0.3:
                    new_conf = list(conf)
                    if new_conf[2] > 55:
                        new_conf[3] = 1.0
                    new_conf = tuple(new_conf)
                    high_conf_entities.append((entity,) + new_conf)
                    high_conf_nums.append(elem_num)

            high_conf_entities = sorted(high_conf_entities, key=lambda x: (x[1], x[4], x[3]), reverse=True)
            for n, elem_num in enumerate(high_conf_nums):
                if elem_num - n >= 0 and elem_num - n < len(top_entities):
                    del top_entities[elem_num - n]
                    del top_conf[elem_num - n]

            log.info(f"top entities {top_entities} top_conf {top_conf}")
            log.info(f"high_conf_entities {high_conf_entities}")

            top_entities = [elem[0] for elem in high_conf_entities] + top_entities
            top_conf = [elem[1:] for elem in high_conf_entities] + top_conf

            log.info(f"top entities {top_entities} top_conf {top_conf}")

            if self.num_entities_to_return == 1 and top_entities:
                entity_ids_list.append(top_entities[0])
                conf_list.append(top_conf[0])
            else:
                entity_ids_list.append(top_entities[: self.num_entities_to_return])
                conf_list.append(top_conf[: self.num_entities_to_return])
        return entity_ids_list, conf_list
