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

import os
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
        num_entities_to_return: int = 10,
        lang: str = "en",
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
        self.num_entities_to_return = num_entities_to_return
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
        self.stemmer = nltk.PorterStemmer()
        self.load()

    def load(self) -> None:
        if not os.path.exists(self.load_path):
            os.makedirs(self.load_path)
        self.conn = sqlite3.connect(str(self.load_path / "custom_database.db"), check_same_thread=False)
        self.cur = self.conn.cursor()
        log.info("Connected to index")

    def save(self) -> None:
        pass

    def add_custom_entities(self, user_id, entity_substr_list, entity_ids_list, tags_list):
        if self.conn is None:
            if not os.path.exists(self.load_path):
                os.makedirs(self.load_path)
            self.conn = sqlite3.connect(str(self.load_path / "custom_database.db"), check_same_thread=False)
            self.cur = self.conn.cursor()
            self.cur.execute("CREATE VIRTUAL TABLE IF NOT EXISTS inverted_index USING fts5(title, entity_id, num_rels "
                             "UNINDEXED, tag, user_id, tokenize = 'porter ascii');")

        for entity_substr, entity_id, tag in zip(entity_substr_list, entity_ids_list, tags_list):
            entity_id = entity_id.replace("/", "slash").replace("-", "hyphen")
            query_str = f"title:{entity_substr} AND tag:{tag} AND user_id:{user_id}"

            query = "SELECT * FROM inverted_index WHERE inverted_index MATCH ?;"
            res = self.cur.execute(query, (query_str,)).fetchall()
            if res and res[0][3] == "name" and res[0][1] == entity_id and tag == "name":
                query = "DELETE FROM inverted_index WHERE entity_id=? AND tag=? AND user_id=?;"
                self.cur.execute(query, (entity_id, tag, user_id))
                self.cur.execute("INSERT INTO inverted_index "
                                 "VALUES (?, ?, ?, ?, ?);", (entity_substr.lower(), entity_id, 1, tag, user_id))
                self.conn.commit()
            elif not res:
                self.cur.execute("INSERT INTO inverted_index "
                                 "VALUES (?, ?, ?, ?, ?);", (entity_substr.lower(), entity_id, 1, tag, user_id))
                self.conn.commit()

    def __call__(
        self,
        user_ids: List[str],
        entity_substr_batch: List[List[str]],
        entity_tags_batch: List[List[str]] = None,
        sent_batch: List[List[str]] = None,
        entity_offsets_batch: List[List[List[int]]] = None,
        sent_offsets_batch: List[List[Tuple[int, int]]] = None,
    ):
        if sent_offsets_batch is None and sent_batch is not None:
            sent_offsets_batch = []
            for sent_list in sent_batch:
                sent_offsets_list = []
                start = 0
                for sentence in sent_list:
                    end = start + len(sentence)
                    sent_offsets_list.append([start, end])
                    start = end + 1
                sent_offsets_batch.append(sent_offsets_list)

        if sent_batch is None:
            sent_batch = [[] for _ in entity_substr_batch]
            sent_offsets_batch = [[] for _ in entity_substr_batch]

        log.info(f"sent_batch {sent_batch}")
        if entity_offsets_batch is None and sent_batch is not None:
            entity_offsets_batch = []
            for entity_substr_list, sent_list in zip(entity_substr_batch, sent_batch):
                text = " ".join(sent_list).lower()
                log.info(f"text {text}")
                entity_offsets_list = []
                for entity_substr in entity_substr_list:
                    st_offset = text.find(entity_substr.lower())
                    end_offset = st_offset + len(entity_substr)
                    entity_offsets_list.append([st_offset, end_offset])
                entity_offsets_batch.append(entity_offsets_list)

        entity_ids_batch, entity_conf_batch, entity_id_tags_batch = [], [], []
        for user_id, entity_substr_list, entity_offsets_list, entity_tags_list, sent_list, sent_offsets_list in zip(
            user_ids, entity_substr_batch, entity_offsets_batch, entity_tags_batch, sent_batch, sent_offsets_batch
        ):
            entity_ids_list, entity_conf_list, entity_id_tags_list = self.link_entities(
                user_id,
                entity_substr_list,
                entity_offsets_list,
                entity_tags_list,
                sent_list,
                sent_offsets_list,
            )
            log.info(f"user_id: {user_id} entity_ids_list: {entity_ids_list} entity_conf_list: {entity_conf_list}")
            
            entity_ids_batch.append(entity_ids_list[:self.num_entities_to_return])
            entity_conf_batch.append(entity_conf_list[:self.num_entities_to_return])
            entity_id_tags_batch.append(entity_id_tags_list[:self.num_entities_to_return])
        return entity_ids_batch, entity_conf_batch, entity_id_tags_batch

    def link_entities(
        self,
        user_id: str,
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
        entity_ids_list, conf_list, entity_id_tags_list = [], [], []
        if entity_substr_list:
            entities_scores_list = []
            cand_ent_scores_list = []
            for entity_substr, tags in zip(entity_substr_list, entity_tags_list):
                for symb_old, symb_new in [("'", "''"), ("-", " "), ("@", ""), (".", ""), ("  ", " ")]:
                    entity_substr = entity_substr.replace(symb_old, symb_new)
                cand_ent_init = defaultdict(set)
                if len(entity_substr) > 1:
                    for start in ["a ", "the ", "my ", "his ", "her "]:
                        if entity_substr.startswith(start):
                            entity_substr = entity_substr[len(start):]
                    cand_ent_init = self.find_exact_match(user_id, entity_substr, tags)
                    clean_tags = [tag for tag, conf in tags]
                    entity_substr_split = [
                        word for word in entity_substr.split(" ") if word not in self.stopwords and len(word) > 0
                    ]
                    if len(entity_substr_split) == 1 and self.stemmer.stem(entity_substr) != entity_substr:
                        entity_substr_stemmed = self.stemmer.stem(entity_substr)
                        stem_cand_ent_init = self.find_exact_match(user_id, entity_substr_stemmed, tags)
                        cand_ent_init = {**cand_ent_init, **stem_cand_ent_init}
                    if not cand_ent_init and len(entity_substr_split) > 1:
                        cand_ent_init = self.find_fuzzy_match(user_id, entity_substr_split, tags)
                    if not cand_ent_init:
                        cand_ent_init = self.find_exact_match(user_id, entity_substr)
                    if not cand_ent_init:
                        cand_ent_init = self.find_fuzzy_match(user_id, entity_substr_split)

                cand_ent_scores = []
                for entity in cand_ent_init:
                    entities_scores = list(cand_ent_init[entity])
                    entities_scores = sorted(entities_scores, key=lambda x: (x[0], x[2], x[1]), reverse=True)
                    cand_ent_scores.append(([entity] + list(entities_scores[0])))

                cand_ent_scores = sorted(cand_ent_scores, key=lambda x: (x[1], x[3], x[2]), reverse=True)
                entity_ids = [elem[0] for elem in cand_ent_scores]
                confs = [elem[1:4] for elem in cand_ent_scores]
                entity_id_tags = [elem[4] for elem in cand_ent_scores]
                entity_ids = [entity_id.replace("slash", "/").replace("hyphen", "-") for entity_id in entity_ids]
                entity_ids_list.append(entity_ids)
                conf_list.append(confs)
                entity_id_tags_list.append(entity_id_tags)

        return entity_ids_list, conf_list, entity_id_tags_list

    def process_cand_ent(self, cand_ent_init, entities_and_ids, entity_substr_split, tags):
        if tags:
            for entity_title, entity_id, entity_rels, f_tag, user_id in entities_and_ids:
                for tag, tag_conf in tags:
                    if tag == f_tag:
                        substr_score = self.calc_substr_score(entity_title, entity_substr_split)
                        cand_ent_init[entity_id].add((substr_score, entity_rels, tag_conf, f_tag))
        else:
            for entity_title, entity_id, entity_rels, f_tag, user_id in entities_and_ids:
                substr_score = self.calc_substr_score(entity_title, entity_substr_split)
                cand_ent_init[entity_id].add((substr_score, entity_rels, 1.0, f_tag))
        return cand_ent_init

    def find_exact_match(self, user_id, entity_substr, tags=None):
        entity_substr = entity_substr.lower()
        entity_substr_split = entity_substr.split()
        cand_ent_init = defaultdict(set)

        query_str = f"title:{entity_substr} AND user_id:{user_id}"
        query = "SELECT * FROM inverted_index WHERE inverted_index MATCH ?;"
        res = self.cur.execute(query, (query_str,))
        entities_and_ids = res.fetchall()
        
        if entities_and_ids:
            cand_ent_init = self.process_cand_ent(cand_ent_init, entities_and_ids, entity_substr_split, tags)
        return cand_ent_init

    def find_fuzzy_match(self, user_id, entity_substr_split, tags=None):
        entity_substr_split = [word.lower() for word in entity_substr_split]
        cand_ent_init = defaultdict(set)
        for word in entity_substr_split:
            query_str = f"title:{word} AND user_id:{user_id}"
            query = "SELECT * FROM inverted_index WHERE inverted_index MATCH ?;"
            res = self.cur.execute(query, (query_str,))
            part_entities_and_ids = res.fetchall()
            cand_ent_init = self.process_cand_ent(cand_ent_init, part_entities_and_ids, entity_substr_split, tags)
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
