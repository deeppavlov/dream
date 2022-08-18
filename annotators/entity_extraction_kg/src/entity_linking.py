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

import copy
import json
import os
import re
import sqlite3
import time
from logging import getLogger
from typing import List, Dict, Tuple, Union, Any
from collections import defaultdict

import pymorphy2
from nltk.corpus import stopwords
from rapidfuzz import fuzz
from deeppavlov_kg import KnowledgeGraph

from deeppavlov.core.common.registry import register
from deeppavlov.core.models.component import Component
from deeppavlov.core.models.serializable import Serializable
from deeppavlov.core.commands.utils import expand_path
from deeppavlov.core.common.file import load_pickle, save_pickle
from src.torch_transformers_el_ranker import TorchTransformersEntityRankerInfer
from src.queries import add_entity_query, create_table_query, insert_entity_query, inv_index_query, add_info_query

log = getLogger(__name__)


@register('entity_linker')
class EntityLinker(Component, Serializable):
    """
        Class for linking of entity substrings in the document to entities in Wikidata
    """

    def __init__(self, load_path: str,
                 entities_database_filename: str = None,
                 num_entities_for_conn_ranking: int = 50,
                 entity_ranker = None,
                 num_entities_to_return: int = 10,
                 max_text_len: int = 300,
                 lang: str = "ru",
                 use_descriptions: bool = True,
                 use_tags: bool = False,
                 lemmatize: bool = False,
                 full_paragraph: bool = False,
                 use_connections: bool = False,
                 log_to_file: bool = False,
                 conn_rank_mode: str = "all",
                 edges_rank: bool = False,
                 ignore_tags: bool = False,
                 delete_hyphens: bool = False,
                 db_format: str = "sqlite",
                 name_to_q_filename: str = None,
                 word_to_q_filename: str = None,
                 entity_ranking_dict_filename: str = None,
                 entity_to_tag_filename: str = None,
                 q_to_name_filename: str = None,
                 p131_filename: str = None,
                 p641_filename: str = None,
                 types_dict_filename: str = None,
                 q_to_page_filename: str = None,
                 wikidata_filename: str = None,
                 occ_labels_filename: str = None,
                 return_additional_info: bool = False,
                 tags_filename: str = None,
                 add_info_filename: str = None,
                 num_entities_for_bert_ranking: int = 10,
                 **kwargs) -> None:
        """

        Args:
            load_path: path to folder with inverted index files
            entity_ranker: component deeppavlov.models.kbqa.rel_ranking_bert
            num_entities_for_conn_ranking: number of candidate entities for ranking using Wikidata KG
            ngram_range: char ngrams range for TfidfVectorizer
            num_entities_to_return: number of candidate entities for the substring which are returned
            lang: russian or english
            use_description: whether to perform entity ranking by context and description
            lemmatize: whether to lemmatize tokens
            **kwargs:
        """
        super().__init__(save_path=None, load_path=load_path)
        self.morph = pymorphy2.MorphAnalyzer()
        self.lemmatize = lemmatize
        self.entities_database_filename = entities_database_filename
        self.entity_ranker = entity_ranker
        self.num_entities_for_conn_ranking = num_entities_for_conn_ranking
        self.num_entities_to_return = num_entities_to_return
        self.max_text_len = max_text_len
        self.lang = f"@{lang}"
        if self.lang == "@en":
            self.stopwords = set(stopwords.words("english"))
        elif self.lang == "@ru":
            self.stopwords = set(stopwords.words("russian"))
        self.not_found_str = "not in wiki"
        self.use_descriptions = use_descriptions
        self.use_connections = use_connections
        self.conn_rank_mode = conn_rank_mode
        self.log_to_file = log_to_file
        self.use_tags = use_tags
        self.full_paragraph = full_paragraph
        self.edges_rank = edges_rank
        self.ignore_tags = ignore_tags
        self.delete_hyphens = delete_hyphens
        self.re_tokenizer = re.compile(r"[\w']+|[^\w ]")
        self.correct_tags_dict = {"PERSON": "PER"}
        self.related_tags = {"LOC": ["GPE"], "GPE": ["LOC"], "WORK_OF_ART": ["PRODUCT", "LAW"],
                             "PRODUCT": ["WORK_OF_ART"], "LAW": ["WORK_OF_ART"], "ORG": ["FAC", "BUSINESS"],
                             "BUSINESS": ["ORG"]}
        self.types_ent = {"p641": "Q31629"}
        self.using_custom_db = False
        self.db_format = db_format
        self.name_to_q_filename = name_to_q_filename
        self.word_to_q_filename = word_to_q_filename
        self.entity_ranking_dict_filename = entity_ranking_dict_filename
        self.entity_to_tag_filename = entity_to_tag_filename
        self.q_to_name_filename = q_to_name_filename
        self.p131_filename = p131_filename
        self.p641_filename = p641_filename
        self.types_dict_filename = types_dict_filename
        self.q_to_page_filename = q_to_page_filename
        self.wikidata_filename = wikidata_filename
        self.occ_labels_filename = occ_labels_filename
        self.return_additional_info = return_additional_info
        self.tags_filename = tags_filename
        self.add_info_filename = add_info_filename
        self.num_entities_for_bert_ranking = num_entities_for_bert_ranking
        self.load()
        self.sum_tm = 0.0
        self.num_entities = 0

    def load(self) -> None:
        if self.db_format == "sqlite":
            if self.tags_filename:
                fl = open(str(expand_path(self.tags_filename)), 'r')
                lines = fl.readlines()
                tags = []
                for line in lines:
                    tags.append(line.strip().split()[0])
                if "O" in tags:
                    tags.remove("O")
                for tag in ["ACTOR", "ATHLETE", "MUSICIAN", "POLITICIAN", "WRITER", "POLITICIAN", "PAINTER", "ENTREPRENEUR"]:
                    if tag in tags:
                        tags.remove(tag)
                for tag in ["MISC", "PERSON"]:
                    if tag not in tags:
                        tags.append(tag)
                self.cursors = {}
                for tag in tags:
                    conn = sqlite3.connect(f"{self.load_path}/{tag.lower()}.db", check_same_thread=False)
                    cur = conn.cursor()
                    self.cursors[tag.lower()] = cur
                conn = sqlite3.connect(str(self.load_path / self.add_info_filename), check_same_thread=False)
                self.add_info_cur = conn.cursor()
            else:
                self.conn = sqlite3.connect(str(self.load_path / self.entities_database_filename), check_same_thread=False)
                self.cur = self.conn.cursor()
            self.occ_labels_dict = load_pickle(expand_path(self.occ_labels_filename))
        else:
            self.name_to_q = load_pickle(self.load_path / self.name_to_q_filename)
            log.info("opened name_to_q")
            self.word_to_q = load_pickle(self.load_path / self.word_to_q_filename)
            log.info("opened word_to_q")
            self.entity_ranking_dict = load_pickle(self.load_path / self.entity_ranking_dict_filename)
            self.entity_to_tag = load_pickle(self.load_path / self.entity_to_tag_filename)
            self.q_to_name = load_pickle(self.load_path / self.q_to_name_filename)
            log.info("opened q_to_name")
            self.p131_dict = load_pickle(self.load_path / self.p131_filename)
            self.p641_dict = load_pickle(self.load_path / self.p641_filename)
            self.types_dict = load_pickle(self.load_path / self.types_dict_filename)
            self.q_to_page = load_pickle(self.load_path / self.q_to_page_filename)
            self.wikidata = load_pickle(self.load_path / self.wikidata_filename)
            log.info("opened wikidata")

    def save(self) -> None:
        pass
    
    def add_entity(self, entity_label, entity, num_rels, tag, page, types_str=None, p131_obj=None,
                         p641_obj=None, triplets_str=None):
        if types_str is None:
            types_str = ""
        if p131_obj is None:
            p131_obj = ""
        if p641_obj is None:
            p641_obj = ""
        if triplets_str is None:
            triplets_str = ""
        self.cur.execute(add_entity_query, (entity_label, entity, num_rels, tag, page, types_str, p131_obj,
                                            p641_obj, triplets_str))
        self.conn.commit()
    
    def insert_data_into_database(self, labels_dict, types_dict, triplets_dict, type_to_tag_dict = None):
        if type_to_tag_dict is None:
            self.type_to_tag_dict = {}
        else:
            self.type_to_tag_dict = type_to_tag_dict
        self.using_custom_db = True
        if not self.tags_filename:
            self.conn.close()
        i = 0
        while True:
            db_path = self.load_path / f"custom_database{i}.db"
            if not db_path.exists():
                break
            i += 1
        log.info(f"labels_dict {labels_dict}")
        
        tags_set = set()
        custom_db_elements = []
        for entity in labels_dict:
            num_rels = 0
            labels = labels_dict[entity]
            types = types_dict.get(entity, [])
            if isinstance(types, list):
                types_str = " ".join(types)
            else:
                types_str = types
            cur_triplets_dict = {}
            cur_triplets = triplets_dict.get(entity, [])
            for rel, obj in cur_triplets:
                if rel in cur_triplets_dict:
                    cur_triplets_dict[rel].append(obj)
                else:
                    cur_triplets_dict[rel] = [obj]
                num_rels += 1
            cur_triplets_list = []
            for rel, obj_list in cur_triplets_dict.items():
                cur_triplets_list.append([rel] + obj_list)
            cur_triplets_list = [" ".join(triplet) for triplet in cur_triplets_list]
            triplets_str = "---".join(cur_triplets_list)
            tag = "MISC"
            if types and types[0] in self.type_to_tag_dict:
                tag = self.type_to_tag_dict[types[0]]
            tags_set.add(tag)
            custom_db_elements.append([labels, entity, num_rels, tag, types_str, triplets_str])
        
        self.conn_dict = {}
        for tag in tags_set:
            conn = sqlite3.connect(f"{self.load_path}/custom_{tag.lower()}.db", check_same_thread=False)
            self.conn_dict[f"custom_{tag.lower()}"] = conn
            cur = conn.cursor()
            cur.execute(create_table_query)
            self.cursors[f"custom_{tag.lower()}"] = cur
        
        for labels, entity, num_rels, tag, types_str, triplets_str in custom_db_elements:
            for entity_label in labels:
                self.cursors[f"custom_{tag.lower()}"].execute(insert_entity_query, (entity_label.lower(),
                    entity, num_rels, tag, "", "", "", "", types_str, "", "", triplets_str))
        
        for tag in tags_set:
            self.conn_dict[f"custom_{tag.lower()}"].commit()
    
    def parse_custom_database(self, elements_list, label_relation, type_relation, type_to_tag_dict):
        labels_dict = {}
        triplets_dict = {}
        types_dict = {}
        for triplet in elements_list:
            subj, rel, obj, *_ = triplet.strip().split("> ")
            subj = subj.strip("<>")
            rel = rel.strip("<>")
            if obj.endswith(" ."):
                obj = obj[:-2]
            obj = obj.strip("<>").strip('"')
            if rel == label_relation:
                if obj in labels_dict:
                    labels_dict[subj].append(obj)
                else:
                    labels_dict[subj] = [obj]
            elif type_relation and rel == type_relation:
                if subj in types_dict:
                    types_dict[subj].append(obj)
                else:
                    types_dict[subj] = [obj]
            else:
                if subj in triplets_dict:
                    triplets_dict[subj].append([rel, obj])
                else:
                    triplets_dict[subj] = [[rel, obj]]

        self.insert_data_into_database(labels_dict, types_dict, triplets_dict, type_to_tag_dict)
    
    def parse_custom_kg_svc(self,
        ontology_url: str = "bolt://neo4j:neo4j@localhost:7687",
        ontology_kinds_hierarchy_path: str = "/root/.deeppavlov/downloads/deeppavlov_kg/database/ontology_kinds_hierarchy.pickle",
        ontology_data_model_path: str = "/root/.deeppavlov/downloads/deeppavlov_kg/database/ontology_data_model.json",
        db_ids_file_path: str = "/root/.deeppavlov/downloads/deeppavlov_kg/database/db_ids.txt"
    ):
        self.graph = KnowledgeGraph(
            ontology_url,
            ontology_kinds_hierarchy_path=ontology_kinds_hierarchy_path,
            ontology_data_model_path=ontology_data_model_path,
            db_ids_file_path=db_ids_file_path
        )
        labels_dict, types_dict, triplets_dict = {}, {}, {}
        nodes_list = self.graph.search_for_entities()
        
        entities_list = []
        for nodes in nodes_list:
            for node in nodes:
                entity_id = node.id
                properties = node._properties
                labels = set(node.labels)
                if "name" in properties and [labels, properties] not in entities_list:
                    names = [properties["name"]]
                    labels_dict[entity_id] = names
                    if "type" in properties:
                        entity_type = properties["type"]
                    elif "kind" in properties:
                        entity_type = properties["kind"]
                    else:
                        entity_type = ""
                    types_dict[entity_id] = entity_type
                    entities_list.append([labels, properties])

        with open(ontology_data_model_path) as fl:
            ontology_data_model = json.load(fl)
        all_rels = set(ontology_data_model.keys())
        
        for rel in all_rels:
            triplets = self.graph.search_relationships(rel)
            for triplet in triplets:
                subj = triplet[0].get("Id")
                cur_rel = triplet[1].type
                obj = triplet[4].get("Id")
                if subj in triplets_dict:
                    triplets_dict[subj].append([cur_rel, obj])
                else:
                    triplets_dict[subj] = [[cur_rel, obj]]

        self.insert_data_into_database(labels_dict, types_dict, triplets_dict)

    def __call__(self, entity_substr_batch: List[List[str]],
                       sentences_batch: List[List[str]] = None,
                       entity_offsets_batch: List[List[List[int]]] = None,
                       sentences_offsets_batch: List[List[Tuple[int, int]]] = None):
        entity_substr_batch = [[entity_substr.lower() for entity_substr in entity_substr_list]
                               for entity_substr_list in entity_substr_batch]
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
        text_batch = [" ".join(sentences_list) for sentences_list in sentences_batch]
        if entity_offsets_batch is None and sentences_batch is not None:
            entity_offsets_batch = []
            for entity_substr_list, sentences_list in zip(entity_substr_batch, sentences_batch):
                entity_offsets_list = self.entity_offsets(entity_substr_list, sentences_list)
                entity_offsets_batch.append(entity_offsets_list)
        
        for n, (entity_substr_list, sentences_list, entity_offsets_list) in \
                enumerate(zip(entity_substr_batch, sentences_batch, entity_offsets_batch)):
            if entity_offsets_list is None:
                entity_offsets_list = self.entity_offsets(entity_substr_list, sentences_list)
                entity_offsets_batch[n] = entity_offsets_list
        
        log.info(f"text_batch {text_batch} entity_offsets_batch {entity_offsets_batch}")
        # (proba, entity_tag)
        tags_with_probas_batch = self.entity_ranker(text_batch, entity_offsets_batch, entity_substr_batch)
        entity_sent_batch = []
        for entity_offsets_list, sentences_offsets_list in zip(entity_offsets_batch, sentences_offsets_batch):
            entity_sent_list = []
            for ent_start, ent_end in entity_offsets_list:
                found_n = -1
                for n, (sent_start, sent_end) in enumerate(sentences_offsets_list):
                    if ent_start >= sent_start and ent_end <= sent_end:
                        found_n = n
                entity_sent_list.append(found_n)
            entity_sent_batch.append(entity_sent_list)
        
        entity_ids_batch, entity_tags_batch, entity_conf_batch, entity_pages_batch, wiki_types_batch = [], [], [], [], []
        for entity_substr_list, entity_offsets_list, entity_sent_list, sentences_list, \
                sentences_offsets_list, tags_with_probas_list in \
                zip(entity_substr_batch, entity_offsets_batch, entity_sent_batch, sentences_batch,
                    sentences_offsets_batch, tags_with_probas_batch):
            entity_ids_list, substr_tags_list, entity_conf_list, entity_tags_list, entity_pages_list, wiki_types_list = \
                self.link_entities(entity_substr_list, entity_offsets_list, entity_sent_list, tags_with_probas_list,
                                   sentences_list, sentences_offsets_list)
            log.info(f"entity_ids_list {entity_ids_list[:10]} entity_conf_list {entity_conf_list[:10]}")
            entity_ids_batch.append(entity_ids_list)
            entity_tags_batch.append(entity_tags_list)
            entity_conf_batch.append(entity_conf_list)
            entity_pages_batch.append(entity_pages_list)
            wiki_types_batch.append(wiki_types_list)

        images_link_batch, categories_batch, first_par_batch, dbpedia_types_batch = \
            self.extract_additional_info(entity_ids_batch, wiki_types_batch)
        if self.return_additional_info:
            return entity_ids_batch, entity_tags_batch, entity_conf_batch, entity_pages_batch, images_link_batch, \
                categories_batch, first_par_batch, dbpedia_types_batch
        else:
            return entity_ids_batch, entity_tags_batch, entity_conf_batch, entity_pages_batch
    
    def entity_offsets(self, entity_substr_list, sentences_list):
        text = " ".join(sentences_list).lower()
        entity_offsets_list = []
        for entity_substr in entity_substr_list:
            st_offset = text.find(entity_substr.lower())
            end_offset = st_offset + len(entity_substr)
            entity_offsets_list.append([st_offset, end_offset])
        return entity_offsets_list

    def link_entities(self, entity_substr_list: List[str],
                            entity_offsets_list: List[List[int]],
                            entity_sent_list: List[int],
                            tags_with_probas_list: List[Tuple[str, float]],
                            sentences_list: List[str],
                            sentences_offsets_list: List[List[int]]) -> List[List[str]]:
        log.info(f"entity_substr_list {entity_substr_list} tags_with_probas_list {tags_with_probas_list}")
        entity_ids_list, substr_tags_list, conf_list, entity_tags_list, pages_list, \
        wiki_types_list = [], [], [], [], [], []
        if entity_substr_list:
            entities_scores_list = []
            cand_ent_scores_list, cand_ent_scores_init_list = [], []
            entity_substr_split_list = [[word for word in entity_substr.split(' ')
                                   if word not in self.stopwords and len(word) > 1]
                                  for entity_substr in entity_substr_list]
            tm1 = time.time()
            init_cand_ent_scores_list = []
            if self.using_custom_db:
                if not self.type_to_tag_dict:
                    tags_with_probas_list = [[(elem[0][0], "MISC")] for elem in tags_with_probas_list]
                entity_tags_dict, init_cand_ent_scores_dict = self.get_cand_ent_customdb(entity_substr_list,
                    entity_substr_split_list, entity_sent_list, tags_with_probas_list, sentences_list)
            else:
                tm_st = time.time()
                entity_tags_dict, init_cand_ent_scores_dict = self.get_cand_ent_wikidata(entity_substr_list,
                    entity_substr_split_list, entity_sent_list, tags_with_probas_list, sentences_list)
                self.sum_tm += time.time() - tm_st
                self.num_entities += len(entity_substr_list)
                log.warning(f"candidate entities retrieve time: {time.time() - tm_st} --- sum tm {self.sum_tm} "
                            f"num entities {self.num_entities}")
            
            log.info(f"entity_tags_dict {entity_tags_dict}")
            for n in range(len(entity_substr_list)):
                init_cand_ent_scores_list.append(init_cand_ent_scores_dict[n])
                substr_tags_list.append(entity_tags_dict[n])

            entities_types_dict = {}
            for entity_substr, tag, cand_ent_scores in zip(entity_substr_list, substr_tags_list,
                                                           init_cand_ent_scores_list):
                cand_ent_scores_init = sorted(cand_ent_scores, key=lambda x: (x[1][0], x[1][1]), reverse=True)
                cand_ent_scores = cand_ent_scores_init[:self.num_entities_for_conn_ranking]
                cand_ent_scores_list.append(cand_ent_scores)
                cand_ent_scores_init_list.append(cand_ent_scores_init)
                entity_ids = [elem[0] for elem in cand_ent_scores]
                conf = [elem[1][:2] for elem in cand_ent_scores]
                pages = [elem[1][2] for elem in cand_ent_scores]
                entities_scores_list.append({ent: score for ent, score in cand_ent_scores})
                for ent, scores in cand_ent_scores_init:
                    if isinstance(scores[3], str):
                        entities_types_dict[ent] = scores[3].split()
                    else:
                        entities_types_dict[ent] = scores[3]
                entity_ids_list.append(entity_ids)
                conf_list.append(conf)
                pages_list.append(pages)
            if self.use_connections:
                tm1 = time.time()
                entities_with_conn_scores_list, entities_scores_list = \
                    self.rank_by_connections(entity_substr_list, substr_tags_list, entity_sent_list,
                                             cand_ent_scores_list, entities_scores_list)
                
                entity_ids_list, pages_list, entity_tags_list, conf_list, wiki_types_list = self.postprocess_entities(entity_substr_list,
                    entity_substr_split_list, entity_offsets_list, substr_tags_list, entity_sent_list, entities_with_conn_scores_list,
                    entities_types_dict, sentences_list, sentences_offsets_list)
                
        return entity_ids_list, substr_tags_list, conf_list, entity_tags_list, pages_list, wiki_types_list
    
    def get_cand_ent_customdb(self, entity_substr_list, entity_substr_split_list, entity_sent_list,
                                    tags_with_probas_list, sentences_list):
        entity_tags_dict = {}
        init_cand_ent_scores_dict = {n: [] for n in range(len(entity_substr_list))}
        for n, (entity_substr, entity_substr_split, entity_sent, tags_with_probas) in \
                    enumerate(zip(entity_substr_list, entity_substr_split_list, entity_sent_list,
                                  tags_with_probas_list)):
            tags_for_search = self.process_tags_for_search(entity_substr_list, tags_with_probas)
            cand_ent_scores = self.get_cand_ent(entity_substr, entity_substr_split, tags_for_search, entity_sent,
                                                sentences_list, [], [], "custom")
            init_cand_ent_scores_dict[n] = cand_ent_scores
            entity_tags_dict[n] = tags_with_probas[0][1]
        return entity_tags_dict, init_cand_ent_scores_dict
    
    def get_cand_ent_wikidata(self, entity_substr_list, entity_substr_split_list, entity_sent_list,
                                    tags_with_probas_list, sentences_list):
        entity_tags_dict = {}
        init_cand_ent_scores_dict = {n: [] for n in range(len(entity_substr_list))}
        types_of_sport_ent, types_of_sport_tr = set(), set()
        already_found = set()
        for num_iter in range(5):
            for n, (entity_substr, entity_substr_split, entity_sent, tags_with_probas) in \
                    enumerate(zip(entity_substr_list, entity_substr_split_list, entity_sent_list,
                                  tags_with_probas_list)):
                tags_for_search = self.process_tags_for_search(entity_substr_list, tags_with_probas)
                if tags_for_search:
                    tags_for_search = self.correct_tags(entity_substr, tags_for_search, tags_with_probas)
                    tags_by_iter = {0: {"POLITICIAN", "ACTOR", "WRITER", "MUSICIAN", "ATHLETE", "PAINTER", "ENTREPRENEUR", "PER"},
                                    1: {"POLITICIAN", "ACTOR", "WRITER", "MUSICIAN", "ATHLETE", "PAINTER", "ENTREPRENEUR", "PER"},
                                    2: {"SPORTS_SEASON", "CHAMPIONSHIP", "SPORTS_EVENT"}
                                    }
                    if not init_cand_ent_scores_dict[n] and tags_for_search and \
                            ((num_iter == 0 and tags_for_search[0] in tags_by_iter[0]
                              and len(entity_substr.split()) > 1) or
                             (num_iter == 1 and tags_for_search[0] in tags_by_iter[1]
                              and len(entity_substr.split()) == 1) or
                             (num_iter == 2 and tags_for_search[0] in tags_by_iter[2]
                              and len(entity_substr.split()) > 3) or
                             num_iter == 3):
                        is_already_found = False
                        if "PER" in tags_for_search:
                            for already_found_substr in already_found:
                                if set([word.lower() for word
                                        in already_found_substr.split()]).intersection(set([word.lower() for word
                                                                                            in entity_substr.split()])):
                                    is_already_found = True
                                    break
                        cand_ent_scores = []
                        if not is_already_found:
                            tm_sqlite_st = time.time()
                            if tags_for_search:
                                p641_ent, p641_tr = [], []
                                cand_ent_scores = self.get_cand_ent(entity_substr, entity_substr_split,
                                    tags_for_search, entity_sent, sentences_list, p641_ent, p641_tr, "wiki")
                            if cand_ent_scores:
                                cur_ent, (cur_substr_score, cur_num_rels, cur_page, cur_descr, cur_types, cur_p131,
                                    cur_p641, cur_triplets_str, cur_tag) = cand_ent_scores[0]
                                if isinstance(cur_types, str):
                                    cur_types = cur_types.split()
                                if isinstance(cur_p641, str):
                                    cur_p641 = cur_p641.split()
                                p641_ent, p641_tr = self.postprocess_types_for_entity_filter(entity_substr,
                                    entity_sent, tags_for_search, cur_substr_score, cur_types, cur_p641)
                            
                            tm_sqlite_end = time.time()
                            if "PER" in tags_for_search:
                                already_found.add(entity_substr)
                        init_cand_ent_scores_dict[n] = cand_ent_scores
                entity_tags_dict[n] = tags_with_probas[0][1]
        return entity_tags_dict, init_cand_ent_scores_dict
    
    def postprocess_entities(self, entity_substr_list, entity_substr_split_list, entity_offsets_list, substr_tags_list,
                                   entity_sent_list, entities_with_conn_scores_list, entities_types_dict,
                                   sentences_list, sentences_offsets_list):
        entity_types_sent_most_freq, entity_types_most_freq = self.most_freq_types(entity_substr_split_list,
                    substr_tags_list, entity_sent_list, entities_with_conn_scores_list, entities_types_dict)
        
        entity_ids_list, pages_list, ent_tags_list, conf_list, wiki_types_list = [], [], [], [], []
        for entity_substr, entity_substr_split, entity_offsets, tag, entity_sent, entities_with_conn_scores in \
                zip(entity_substr_list, entity_substr_split_list, entity_offsets_list, substr_tags_list,
                    entity_sent_list, entities_with_conn_scores_list):
            top_entities_with_scores = []
            most_freq_type = ""
            freq_types_sent_info = entity_types_sent_most_freq.get((entity_sent, tag), [])
            freq_types_info = entity_types_most_freq.get(tag, [])
            if freq_types_sent_info and freq_types_info and \
                    (freq_types_sent_info[1][0] >= 4 or (freq_types_info[1][0] >= 2
                                                         and freq_types_info[0] == freq_types_sent_info[0])):
                most_freq_type = freq_types_info[0]
            
            for entity, substr_score, num_rels, page, descr, wiki_types, ent_tag, conn_score_notag, \
                conn_score_tag in entities_with_conn_scores:
                add_types_score = 0
                cur_types = entities_types_dict.get(entity, [])
                for cur_type in cur_types:
                    if most_freq_type and cur_type == most_freq_type:
                        add_types_score += 40
            
                if not ent_tag:
                    ent_tag = tag
                top_entities_with_scores.append((entity, substr_score, num_rels, conn_score_notag + add_types_score,
                                                 conn_score_tag, page, wiki_types, ent_tag, descr))
            
            entity_ids = [elem[0] for elem in top_entities_with_scores[:self.num_entities_for_bert_ranking]]
            descrs = [elem[-1] for elem in top_entities_with_scores[:self.num_entities_for_bert_ranking]]
            
            filtered_top_entities_with_scores = []
            for entity, substr_score, num_rels, conn_score_notag, conn_score_tag, page, wiki_types, ent_tag, descr in \
                    top_entities_with_scores:
                filtered_top_entities_with_scores.append([entity, substr_score, num_rels, conn_score_notag,
                                                          conn_score_tag, float(substr_score), page, wiki_types, ent_tag])
            if not filtered_top_entities_with_scores:
                for entity, substr_score, num_rels, conn_score_notag, conn_score_tag, page, wiki_types, ent_tag, descr in \
                        top_entities_with_scores:
                    filtered_top_entities_with_scores.append([entity, substr_score, num_rels, conn_score_notag,
                                                              conn_score_tag, float(substr_score), page, wiki_types, ent_tag])
            top_entities_with_scores = filtered_top_entities_with_scores
            
            if len(entity_substr_split) >= 4 or tag in {"TYPE_OF_SPORT", "ORG"}:
                top_entities_with_scores = sorted(top_entities_with_scores, key=lambda x: (x[1], x[3], x[4], x[2]), reverse=True)
            else:
                top_entities_with_scores = sorted(top_entities_with_scores, key=lambda x: (x[3], x[4], x[1], x[2]), reverse=True)
            
            num_year_entities = 0
            for ent in top_entities_with_scores[:5]:
                if re.findall(r"[\d]{4}", ent[-1]):
                    num_year_entities += 1
            
            if len(top_entities_with_scores) > 1:
                edges_0 = top_entities_with_scores[0][3] + top_entities_with_scores[0][4]
                edges_1 = top_entities_with_scores[1][3] + top_entities_with_scores[1][4]
                
                if top_entities_with_scores[1][1] > 0.9 and \
                    (top_entities_with_scores[0][1] < 0.35 or (top_entities_with_scores[0][1] < 0.68 and edges_1 / edges_0 > 0.8)):
                    new_top_entities_with_scores = [top_entities_with_scores[1], top_entities_with_scores[0]]
                    if len(top_entities_with_scores) > 2:
                        new_top_entities_with_scores += top_entities_with_scores[2:]
                    top_entities_with_scores = new_top_entities_with_scores
                
                if tag == "NATION" and top_entities_with_scores[0][1] < 0.35:
                    for elem in top_entities_with_scores[1:]:
                        if elem[1] == 1.0:
                            top_entities_with_scores = [elem]
                            break
            
            if top_entities_with_scores and top_entities_with_scores[0][1] < 0.35:
                for n_elem in range(len(top_entities_with_scores)):
                    if n_elem > 0 and top_entities_with_scores[n_elem][1] >= 0.9 and top_entities_with_scores[n_elem][5] > 0.8:
                        new_entities_with_scores = [top_entities_with_scores[n_elem]] + top_entities_with_scores[:n_elem]
                        if len(top_entities_with_scores) > n_elem:
                            new_entities_with_scores += top_entities_with_scores[n_elem + 1:]
                        top_entities_with_scores = new_entities_with_scores
                        break
            
            if len(top_entities_with_scores) > 1:
                first_ent = top_entities_with_scores[0]
                second_ent = top_entities_with_scores[1]
                else_ent = []
                if len(top_entities_with_scores) > 2:
                    else_ent = top_entities_with_scores[2:]
                if first_ent[1] <= second_ent[1] and second_ent[2] / max(first_ent[2], 1) > 2 \
                        and (second_ent[3] + second_ent[4]) / 2 > (first_ent[3] + first_ent[4]) / 2:
                    top_entities_with_scores = [second_ent, first_ent] + else_ent

            entity_ids = [elem[0] for elem in top_entities_with_scores]
            confs = [elem[1:6] for elem in top_entities_with_scores]
            final_confs = [elem[5] for elem in top_entities_with_scores]
            ent_tags = [elem[-1].lower() for elem in top_entities_with_scores]
            wiki_types = [elem[-2] for elem in top_entities_with_scores]
            pages = [elem[-3] for elem in top_entities_with_scores]
            
            low_conf = False
            if confs and confs[0][0] < 0.3 and confs[0][4] < 0.51 and not self.using_custom_db:
                low_conf = True
            if not low_conf:
                entity_ids_list.append(copy.deepcopy(entity_ids[:self.num_entities_to_return]))
                pages_list.append(copy.deepcopy(pages[:self.num_entities_to_return]))
                conf_list.append(copy.deepcopy(final_confs[:self.num_entities_to_return]))
                ent_tags_list.append(copy.deepcopy(ent_tags[:self.num_entities_to_return]))
                wiki_types_list.append(copy.deepcopy(wiki_types[:self.num_entities_to_return]))
            else:
                entity_ids_list.append([""])
                pages_list.append([""])
                conf_list.append([0.0])
                if ent_tags:
                    ent_tags_list.append([ent_tags[0]])
                else:
                    ent_tags_list.append([""])
                wiki_types_list.append([""])
        
        corr_ids_list, corr_pages_list, corr_tags_list, corr_conf_list, corr_wiki_types_list = \
            self.correct_already_found(entity_substr_list, entity_ids_list, pages_list, substr_tags_list,
                                       ent_tags_list, conf_list, wiki_types_list)
        
        return corr_ids_list, corr_pages_list, corr_tags_list, corr_conf_list, corr_wiki_types_list
    
    def correct_already_found(self, entity_substr_list, entity_ids_list, pages_list, substr_tags_list,
                                    entity_tags_list, conf_list, wiki_types_list):
        already_found = {}
        for entity_substr, entity_ids, pages, substr_tags, entity_tags, confs, wiki_types in \
                zip(entity_substr_list, entity_ids_list, pages_list, substr_tags_list, entity_tags_list,
                    conf_list, wiki_types_list):
            if len(entity_substr.split()) > 1 and "PER" in substr_tags:
                already_found[entity_substr.lower()] = [entity_ids, pages, entity_tags, confs, wiki_types]
        
        corr_ids_list, corr_pages_list, corr_tags_list, corr_conf_list, corr_wiki_types_list = [], [], [], [], []
        for entity_substr, entity_ids, substr_tags, entity_tags, pages, confs, wiki_types in \
                zip(entity_substr_list, entity_ids_list, substr_tags_list, entity_tags_list, pages_list,
                    conf_list, wiki_types_list):
            already_existing = ""
            if not entity_ids and "PER" in substr_tags:
                for already_found_substr in already_found:
                    if set([word.lower() for word
                            in already_found_substr.split()]).intersection(set([word.lower() for word
                                                                                in entity_substr.split()])):
                        already_existing = already_found_substr
                        break
            if already_existing:
                corr_ids_list.append(already_found[already_existing][0])
                corr_pages_list.append(already_found[already_existing][1])
                corr_tags_list.append(already_found[already_existing][2])
                corr_conf_list.append(already_found[already_existing][3])
                corr_wiki_types_list.append(already_found[already_existing][4])
            else:
                corr_ids_list.append(entity_ids)
                corr_pages_list.append(pages)
                corr_tags_list.append(entity_tags)
                corr_conf_list.append(confs)
                corr_wiki_types_list.append(wiki_types)
        return corr_ids_list, corr_pages_list, corr_tags_list, corr_conf_list, corr_wiki_types_list
    
    def calc_confs(self, conf_list, num_ent):
        final_conf_list = []
        if conf_list:
            if (conf_list[0][0] == 1.0 and (conf_list[0][1] > 29 or conf_list[0][2] > 10 or num_ent == 1)) \
                    or conf_list[0][2] > 200:
                first_conf = 1.0
            else:
                first_conf = 0.0
                if conf_list[0][1] > 0.0:
                    first_conf += 0.5 * min(conf_list[0][1] / 50, 1.0)
                if conf_list[0][2] > 0.0:
                    first_conf += 0.5 * min(conf_list[0][2] / 200, 1.0)
            final_conf_list.append(round(first_conf, 2))

            max_num_rels = max([conf_elem[1] for conf_elem in conf_list])
            max_edge_conf = max([conf_elem[2] for conf_elem in conf_list])
            for conf_elem in conf_list[1:]:
                if (conf_elem[0] == 1.0 and conf_elem[1] > 29) or conf_elem[2] > 200:
                    cur_conf = 0.99
                else:
                    cur_conf = 0.0
                    if max_num_rels > 0:
                        cur_conf = 0.49 * min(conf_elem[1] / max_num_rels, 1.0)
                    if max_edge_conf > 0.0:
                        cur_conf += 0.49 * min(conf_elem[1] / max_edge_conf, 1.0)
                final_conf_list.append(round(cur_conf, 2))
            if len(final_conf_list) > 2:
                for _ in range(20):
                    for i in range(len(final_conf_list) - 2):
                        if final_conf_list[i + 1] < final_conf_list[i + 2]:
                            final_conf_list[i + 1] = round(min(final_conf_list[i + 2] + 0.01, 0.99), 2)
        return final_conf_list

    def most_freq_types(self, entity_substr_split_list, entity_tags_list, entity_sent_list,
                              entities_with_conn_scores_list, entities_types_dict):
        entity_types_sent_freq, entity_types_freq = defaultdict(dict), defaultdict(dict)
        for entity_substr_split, tag, entity_sent, entities_with_conn_scores in \
                zip(entity_substr_split_list, entity_tags_list, entity_sent_list, entities_with_conn_scores_list):
            if entities_with_conn_scores:
                init_substr_score = entities_with_conn_scores[0][1]
                cur_types_dict = {}
                for entity, substr_score, num_rels, *_ in entities_with_conn_scores:
                    if substr_score == init_substr_score:
                        cur_types = entities_types_dict.get(entity, [])
                        for cur_type in cur_types:
                            cur_types_dict[cur_type] = max(cur_types_dict.get(cur_type, 0), num_rels)
                for cur_type, cur_type_rels in cur_types_dict.items():
                    if cur_type in entity_types_sent_freq[(entity_sent, tag)]:
                        prev_type_cnt, prev_type_rels = entity_types_sent_freq[(entity_sent, tag)][cur_type]
                        entity_types_sent_freq[(entity_sent, tag)][cur_type] = (prev_type_cnt + 1,
                                                                                prev_type_rels + cur_type_rels)
                    else:
                        entity_types_sent_freq[(entity_sent, tag)][cur_type] = (1, cur_type_rels)
                    
                    if cur_type in entity_types_freq[tag]:
                        prev_type_cnt, prev_type_rels = entity_types_freq[tag][cur_type]
                        entity_types_freq[tag][cur_type] = (prev_type_cnt + 1, prev_type_rels + cur_type_rels)
                    else:
                        entity_types_freq[tag][cur_type] = (1, cur_type_rels)
        
        entity_types_sent_most_freq, entity_types_most_freq = {}, {}
        for (entity_sent, tag), types_freq in entity_types_sent_freq.items():
            types_freq = types_freq.items()
            types_freq = sorted(types_freq, key=lambda x: (x[1][0], x[1][1]), reverse=True)
            if types_freq:
                if len(types_freq) == 1:
                    entity_types_sent_most_freq[(entity_sent, tag)] = types_freq[0]
                else:
                    if abs(types_freq[1][1][0] - types_freq[0][1][0]) == 1 and types_freq[1][1][1] > 100 \
                            and types_freq[0][1][1] < 25:
                        entity_types_sent_most_freq[(entity_sent, tag)] = types_freq[1]
                    else:
                        entity_types_sent_most_freq[(entity_sent, tag)] = types_freq[0]
        
        for tag, types_freq in entity_types_freq.items():
            types_freq = types_freq.items()
            types_freq = sorted(types_freq, key=lambda x: (x[1][0], x[1][1]), reverse=True)
            if types_freq:
                if len(types_freq) == 1:
                    entity_types_most_freq[tag] = types_freq[0]
                else:
                    if abs(types_freq[1][1][0] - types_freq[0][1][0]) == 1 \
                            and types_freq[1][1][1] / types_freq[0][1][1] > 5.0:
                        entity_types_most_freq[tag] = types_freq[1]
                    else:
                        entity_types_most_freq[tag] = types_freq[0]
        return entity_types_sent_most_freq, entity_types_most_freq
    
    def process_tags_for_search(self, entity_substr_list, tags_with_probas):
        tags_for_search = []
        for n_tag, (tag_proba, tag) in enumerate(tags_with_probas):
            if tag_proba > 0.6:
                tags_for_search.append(tag)
                if len(entity_substr_list) <= 2:
                    break
            elif len(entity_substr_list) > 2 and tag_proba > 0.1:
                tags_for_search.append(tag)
        add_tags = []
        for tag in tags_for_search:
            if tag in self.related_tags:
                add_tags += self.related_tags[tag]
        tags_for_search += add_tags
        
        if tags_with_probas and tags_with_probas[0][1] == "PER" and tags_with_probas[0][0] > 0.33:
            tags_for_search.append("PER")
        
        if len(entity_substr_list) == 1 and not tags_for_search:
            for tag_proba, tag in tags_with_probas[:2]:
                tags_for_search.append(tag)
            tags_for_search.append("MISC")
        
        if tags_with_probas and tags_with_probas[0][0] < 0.9 \
                and tags_with_probas[0][1] in {"OCCUPATION", "CHEMICAL_ELEMENT"}:
            tags_for_search.append("MISC")
        tags_for_search = [self.correct_tags_dict.get(tag, tag) for tag in tags_for_search]
        return tags_for_search
    
    def correct_tags(self, entity_substr, tags_for_search, tags_with_probas):
        if tags_for_search[0] in {"POLITICIAN", "ACTOR", "WRITER", "MUSICIAN", "ATHLETE", "PAINTER", "ENTREPRENEUR"} \
                and "PER" not in tags_for_search:
            tags_for_search.append("PER")
        elif tags_for_search[0] == "PER":
            for new_tag in {"POLITICIAN", "ACTOR", "WRITER", "MUSICIAN", "ATHLETE", "PAINTER", "ENTREPRENEUR"}:
                if new_tag not in tags_for_search:
                    tags_for_search.append(new_tag)
        if tags_with_probas[0][1] == "COUNTRY" and (tags_with_probas[1][1] == "SPORTS_EVENT" or
                tags_with_probas[2][1] == "SPORTS_EVENT") and "SPORTS_EVENT" not in tags_for_search:
            tags_for_search.append("SPORTS_EVENT")
        if tags_for_search[0] == "ATHLETE" and re.findall(r"[\d]{3,4}", entity_substr):
            tags_for_search = ["SPORTS_SEASON"]
        if tags_with_probas[0][1] == "SPORT_TEAM" and (tags_with_probas[1][1] == "ASSOCIATION_FOOTBALL_CLUB" or
                tags_with_probas[2][1] == "ASSOCIATION_FOOTBALL_CLUB") \
                and "ASSOCIATION_FOOTBALL_CLUB" not in tags_for_search:
            tags_for_search.append("ASSOCIATION_FOOTBALL_CLUB")
        if tags_for_search[0] == "PRODUCT" and len(entity_substr) <= 2:
            tags_for_search = ["CHEMICAL_ELEMENT"]
        return tags_for_search
    
    def preprocess_types_for_entity_filter(self, entity_sent, sentences_list, p641_ent, p641_tr):
        cur_p641 = set()
        if p641_ent:
            for dist in range(len(sentences_list)):
                for cur_entity_sent, tp in p641_ent:
                    if cur_entity_sent == abs(entity_sent - dist):
                        cur_p641.add(tp)
                if cur_p641:
                    break
        else:
            for dist in range(len(sentences_list)):
                for cur_entity_sent, tp in p641_tr:
                    if cur_entity_sent == abs(entity_sent - dist):
                        cur_p641.add(tp)
                if cur_p641:
                    break
        cur_p641 = list(cur_p641)
        return cur_p641
    
    def postprocess_types_for_entity_filter(self, entity_substr, entity_sent, tags_for_search, cur_substr_score,
                                                  cur_types, cur_p641):
        p641_ent, p641_tr = set(), set()
        if (cur_substr_score == 1.0 and len(entity_substr.split()) > 1
                and tags_for_search[0] in {"POLITICIAN", "ACTOR", "WRITER", "MUSICIAN", "ATHLETE", "PAINTER", "ENTREPRENEUR", "PER"}) or \
                (len(entity_substr.split()) >= 3
                 and tags_for_search[0] in {"SPORTS_EVENT", "CHAMPIONSHIP", "SPORTS_SEASON"}):
            if cur_p641:
                for tp in cur_p641:
                    p641_tr.add((entity_sent, tp))
        return p641_ent, p641_tr
    
    def get_cand_ent(self, entity_substr, entity_substr_split, tags_for_search, entity_sent, sentences_list,
                           p641_ent, p641_tr, db_type):
        cand_ent_scores = []
        cur_p641 = self.preprocess_types_for_entity_filter(entity_sent, sentences_list, p641_ent, p641_tr)
        total_cand_ent_init = {}
        if tags_for_search and tags_for_search[0] not in {"LITERARY_WORK", "SONG", "WORK_OF_ART", "FILM"} \
                and entity_substr.startswith("the "):
            entity_substr = entity_substr[4:]
        
        tm_st = time.time()
        if self.db_format == "sqlite":
            cand_ent_init = self.find_exact_match_sqlite(entity_substr, tags_for_search, {"P641": cur_p641},
                                                         db_type=db_type)
        else:
            cand_ent_init = self.find_exact_match_pickle(entity_substr, tags_for_search, {"P641": cur_p641})
        total_cand_ent_init = {**cand_ent_init, **total_cand_ent_init}
        if entity_substr.startswith("the "):
            entity_substr = entity_substr[4:]
            if self.db_format == "sqlite":
                cand_ent_init = self.find_exact_match_sqlite(entity_substr, tags_for_search, {"P641": cur_p641},
                                                             db_type=db_type)
            else:
                cand_ent_init = self.find_exact_match_pickle(entity_substr, tags_for_search, {"P641": cur_p641})
            total_cand_ent_init = {**cand_ent_init, **total_cand_ent_init}
        
        if len(entity_substr_split) > 1 and (not total_cand_ent_init or (len(total_cand_ent_init) < 3
                                                                         and len(entity_substr_split) > 2)):
            if self.db_format == "sqlite":
                cand_ent_init = self.find_fuzzy_match_sqlite(entity_substr_split, tags_for_search, db_type=db_type)
            else:
                cand_ent_init = self.find_fuzzy_match_pickle(entity_substr_split, tags_for_search)
            total_cand_ent_init = {**cand_ent_init, **total_cand_ent_init}
        
        if tags_for_search and tags_for_search[0] in {"POLITICIAN", "ACTOR", "WRITER", "MUSICIAN", "ATHLETE", "PAINTER", "ENTREPRENEUR", "PER"}:
            for entity in total_cand_ent_init:
                entities_scores = list(total_cand_ent_init[entity])
                entities_scores = sorted(entities_scores, key=lambda x: (x[0], x[1]), reverse=True)
                if entities_scores[0][0] >= 0.9:
                    cand_ent_scores.append((entity, entities_scores[0]))
            if not cand_ent_scores:
                for entity in total_cand_ent_init:
                    entities_scores = list(total_cand_ent_init[entity])
                    entities_scores = sorted(entities_scores, key=lambda x: (x[0], x[1]), reverse=True)
                    if entities_scores[0][0] > 0.4:
                        cand_ent_scores.append((entity, entities_scores[0]))
        else:
            for entity in total_cand_ent_init:
                entities_scores = list(total_cand_ent_init[entity])
                entities_scores = sorted(entities_scores, key=lambda x: (x[0], x[1]), reverse=True)
                if entities_scores[0][0] > 0.29 or \
                        (tags_for_search
                         and tags_for_search[0] in {"NATIONAL_SPORTS_TEAM", "SPORTS_EVENT", "SPORT_TEAM"} and
                         entities_scores[0][0] > 0.1) or \
                        (len(tags_for_search) > 1 and tags_for_search[1] == "SPORTS_EVENT"
                         and entities_scores[0][0] > 0.1) or \
                        (tags_for_search and tags_for_search[0] == "SPORTS_SEASON"
                         and re.findall(r"^[\d]{3,4}", entity_substr)):
                    cand_ent_scores.append((entity, entities_scores[0]))
        
        cand_ent_scores = sorted(cand_ent_scores, key=lambda x: (x[1][0], x[1][1]), reverse=True)
        if self.db_format == "pickle":
            cand_ent_scores = [(entity, entities_scores + (self.wikidata.get(entity, []),))
                               for entity, entities_scores in cand_ent_scores]
        log.info(f"exec time {round(time.time() - tm_st, 2)} {len(cand_ent_scores)}")
        return cand_ent_scores
    
    def make_query_str(self, entity_substr, tags=None, rels_dict=None):
        title_str = ""
        make_query_flag = False
        if isinstance(entity_substr, str):
            entity_substr = entity_substr.replace('.', '').replace(',', '')
            if self.delete_hyphens:
                entity_substr = entity_substr.replace("-", " ").replace("'", " ").replace("&", "")
            if len(entity_substr) > 1:
                make_query_flag = True
            title_str = f"title:{entity_substr}"
        else:
            entity_substr = [elem.replace('.', '').replace(',', '') for elem in entity_substr]
            if all([len(elem) > 0 for elem in entity_substr]):
                entity_substr = [f"title:{elem}" for elem in entity_substr]
                if len(entity_substr) == 2:
                    title_str = f"({' OR '.join(entity_substr)})"
                elif len(entity_substr) > 2:
                    entity_lists = []
                    for i in range(len(entity_substr) - 1):
                        entity_lists.append(" AND ".join(entity_substr[i:i + 2]))
                    for i in range(len(entity_substr) - 2):
                        entity_lists.append(" AND ".join([entity_substr[i], entity_substr[i + 2]]))
                    title_str = f"({' OR '.join(entity_lists)})"
                make_query_flag = True
        rels_str = ""
        if rels_dict:
            rel_str_list = []
            for rel, objects in rels_dict.items():
                if objects:
                    rel = rel.lower()
                    objects_str = [f"{rel}:{obj}" for obj in objects]
                    cur_rel_str = ' OR '.join(objects_str)
                    if len(objects_str) > 1:
                        cur_rel_str = f"({cur_rel_str})"
                    rel_str_list.append(cur_rel_str)
            if rel_str_list:
                rels_str = " AND ".join(rel_str_list)
        
        query_str_list = [title_str]
        
        if tags and not self.tags_filename:
            tags = [f"tag:{tag}" for tag in tags]
            if len(tags) > 1:
                tag_str = f"({' OR '.join(tags)})"
            else:
                tag_str = tags[0]
            query_str_list.append(tag_str)
        
        if rels_str:
            query_str_list.append(rels_str)
        
        query_str = " AND ".join(query_str_list)
        
        return query_str, make_query_flag
    
    def process_cand_ent(self, cand_ent_init, entities_and_ids, entity_substr_split, tags, db_type):
        is_misc = False
        if tags and tags[0] == "MISC":
            is_misc = True
        for cand_entity_title, cand_entity_id, cand_entity_rels, tag, page, descr, entity_title, name_or_alias, \
                types, locations, types_of_sport, triplets_str in entities_and_ids:
            if (is_misc and entity_title and entity_title[0].islower() and db_type == "wiki") or not is_misc \
                    or db_type == "custom":
                substr_score = self.calc_substr_score(cand_entity_id, cand_entity_title, entity_substr_split,
                                                      tags, name_or_alias)
                cand_ent_init[cand_entity_id].add((substr_score, cand_entity_rels, page, descr, types, locations,
                                                   types_of_sport, triplets_str, tag))
        return cand_ent_init
    
    def find_exact_match_sqlite(self, entity_substr, tags, rels_dict=None, db_type="wiki"):
        if self.delete_hyphens:
            for symb in [" s", "'s", " '", " (", " &", ' "', "’s", " ”", " ’"]:
                if entity_substr.endswith(symb):
                    entity_substr = entity_substr.replace(symb, "")
            for symb in [": "]:
                if entity_substr.startswith(symb):
                    entity_substr = entity_substr.replace(symb, "")
            entity_substr = entity_substr.replace("-", " ").replace("'", " ")
        entity_substr_split = entity_substr.split()
        entities_and_ids = []
        cand_ent_init = defaultdict(set)
        entity_substr = entity_substr.replace('.', '').replace(',', '').strip()
        if entity_substr:
            if self.tags_filename:
                for tag in tags:
                    query_str, make_query_flag = self.make_query_str(entity_substr, None, rels_dict)
                    log.info(f"query_str {query_str} entity_substr {entity_substr}")
                    if self.using_custom_db:
                        tag_key = f"custom_{tag.lower()}"
                    else:
                        tag_key = tag.lower()
                    if tag_key in self.cursors and make_query_flag:
                        log.info(f"tag {tag}")
                        res = self.cursors[tag_key].execute(inv_index_query, (query_str,))
                        entities_and_ids = res.fetchall()
                        if entities_and_ids:
                            cand_ent_init = self.process_cand_ent(cand_ent_init, entities_and_ids,
                                                                  entity_substr_split, [tag], db_type)
            else:
                query_str, make_query_flag = self.make_query_str(entity_substr, tags, rels_dict)
                log.info(f"query_str {query_str} entity_substr {entity_substr}")
                if make_query_flag:
                    res = self.cur.execute(inv_index_query, (query_str,))
                    entities_and_ids = res.fetchall()
                    if entities_and_ids:
                        cand_ent_init = self.process_cand_ent(cand_ent_init, entities_and_ids, entity_substr_split,
                                                              tags, db_type)
        if rels_dict and not cand_ent_init:
            if self.tags_filename:
                for tag in tags:
                    if self.using_custom_db:
                        tag_key = f"custom_{tag.lower()}"
                    else:
                        tag_key = tag.lower()
                    query_str, make_query_flag = self.make_query_str(entity_substr)
                    log.info(f"query_str {query_str} entity_substr {entity_substr}")
                    if tag_key in self.cursors and make_query_flag:
                        res = self.cursors[tag_key].execute(inv_index_query, (query_str,))
                        entities_and_ids = res.fetchall()
                        if entities_and_ids:
                            cand_ent_init = self.process_cand_ent(cand_ent_init, entities_and_ids,
                                                                  entity_substr_split, [tag], db_type)
            else:
                query_str, make_query_flag = self.make_query_str(entity_substr, tags)
                log.info(f"query_str {query_str} entity_substr {entity_substr}")
                res = self.cur.execute(inv_index_query, (query_str,))
                entities_and_ids = res.fetchall()
                if entities_and_ids and make_query_flag:
                    cand_ent_init = self.process_cand_ent(cand_ent_init, entities_and_ids, entity_substr_split,
                                                          tags, db_type)
        return cand_ent_init
    
    def find_exact_match_pickle(self, entity_substr, tags, rels_dict=None):
        cand_ids_info = {}
        if entity_substr in self.name_to_q:
            cand_ids = self.name_to_q[entity_substr]
            cand_ids_tags = [(entity_id, self.entity_to_tag.get(entity_id, "MISC")) for entity_id in cand_ids]
            if tags:
                tags = set(tags)
                cand_ids_tags = [elem for elem in cand_ids_tags if elem[1] in tags]
            cand_ids_info = {entity_id: {(1.0, self.entity_ranking_dict.get(entity_id, 0),
                                          self.q_to_page.get(entity_id, ""), tuple(self.types_dict.get(entity_id, [])),
                                          tuple(self.p131_dict.get(entity_id, [])),
                                          tuple(self.p641_dict.get(entity_id, [])))} for entity_id, _ in cand_ids_tags}
        return cand_ids_info
    
    def find_fuzzy_match_pickle(self, entity_substr, tags, rels_dict=None):
        cand_ids_info = {}
        cand_ids_set = set()
        for word in entity_substr:
            if len(word) > 1 and word not in self.stopwords and word in self.word_to_q:
                cand_ids = self.word_to_q[word]
                if tags:
                    tags = set(tags)
                    cand_ids = {entity_id for entity_id in cand_ids
                                if self.entity_to_tag.get(entity_id, "MISC") not in tags}
                cand_ids_set = cand_ids_set.union(cand_ids)
        for entity_id in cand_ids_set:
            names = self.q_to_name.get(entity_id, [])
            num_rels = self.entity_ranking_dict.get(entity_id, 0)
            page = self.q_to_page.get(entity_id, "")
            types = tuple(self.types_dict.get(entity_id, []))
            p131 = tuple(self.p131_dict.get(entity_id, []))
            p641 = tuple(self.p641_dict.get(entity_id, []))
            for name in names:
                substr_score = self.calc_substr_score(entity_id, name, entity_substr, tags)
                if entity_id in cand_ids_info:
                    cand_ids_info[entity_id].add((substr_score, num_rels, page, types, p131, p641))
                else:
                    cand_ids_info[entity_id] = {(substr_score, num_rels, page, types, p131, p641)}
        return cand_ids_info
    
    def find_pages(self, entity_substr, tags, pages):
        if self.delete_hyphens:
            entity_substr = entity_substr.replace("-", " ")
        entity_substr_split = entity_substr.split()
        cand_ent_init = defaultdict(set)
        for page, entity_id in pages:
            tags_for_search = [f"tag:{tag}" for tag in tags]
            if len(tags_for_search) == 1:
                tags_str = tags_for_search[0]
            else:
                tags_str = " OR ".join(tags_for_search)
                tags_str = f"({tags_str})"
            
            if self.delete_hyphens:
                for old_symb, new_symb in [("-", " "), ("@", ""), (".", ""), ("(", ""), (")", ""), ("  ", " ")]:
                    page = page.replace(old_symb, new_symb)
            if entity_id:
                query_str = f"page:{page} AND entity_id:{entity_id} AND {tags_str}"
            else:
                query_str = f"page:{page} AND {tags_str}"
            
            res = self.cur.execute(inv_index_query, (query_str,))
            entities_and_ids = res.fetchall()
            cand_ent_init = self.process_cand_ent(cand_ent_init, entities_and_ids, entity_substr_split, tags)
        
        if not cand_ent_init and self.ignore_tags:
            for page, entity_id in pages:
                if self.delete_hyphens:
                    for old_symb, new_symb in [("-", " "), ("@", ""), (".", ""), ("(", ""), (")", ""), ("  ", " ")]:
                        page = page.replace(old_symb, new_symb)
                if entity_id:
                    query_str = f"page:{page} AND entity_id:{entity_id}"
                else:
                    query_str = f"page:{page}"
                res = self.cur.execute(inv_index_query, (query_str,))
                entities_and_ids = res.fetchall()
                cand_ent_init = self.process_cand_ent(cand_ent_init, entities_and_ids, entity_substr_split, tags)
            
        return cand_ent_init
    
    def find_fuzzy_match_sqlite(self, entity_substr_split, tags, db_type):
        cand_ent_init = defaultdict(set)
        if self.tags_filename and not self.using_custom_db:
            for tag in tags:
                entities_and_ids = []
                query_str = self.make_query_str(entity_substr_split)
                try:
                    if tag.lower() in self.cursors:
                        query = "SELECT * FROM inverted_index WHERE inverted_index MATCH '{}';".format(query_str)
                        res = self.cursors[tag.lower()].execute(query)
                        entities_and_ids = res.fetchall()
                except:
                    pass
                log.info(f"query_str {query_str} entity_substr_split {entity_substr_split} {len(entities_and_ids)}")
                if entities_and_ids:
                    cand_ent_init = self.process_cand_ent(cand_ent_init, entities_and_ids, entity_substr_split, [tag], db_type)
        else:
            query_str = self.make_query_str(entity_substr_split, tags)
            try:
                query = "SELECT * FROM inverted_index WHERE inverted_index MATCH '{}';".format(query_str)
                res = self.cur.execute(query)
                entities_and_ids = res.fetchall()
            except:
                entities_and_ids = []
            log.info(f"query_str {query_str} entity_substr_split {entity_substr_split} {len(entities_and_ids)}")
            if entities_and_ids:
                cand_ent_init = self.process_cand_ent(cand_ent_init, entities_and_ids, entity_substr_split, tags, db_type)
        return cand_ent_init

    def morph_parse(self, word):
        morph_parse_tok = self.morph.parse(word)[0]
        normal_form = morph_parse_tok.normal_form
        return normal_form
        
    def calc_substr_score(self, cand_entity_id, cand_entity_title, entity_substr_split, tags, name_or_alias="name"):
        label_tokens = cand_entity_title.split() 
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
                            found = True
                            break
        substr_score = round(cnt / max(len(label_tokens), len(entity_substr_split)), 3)
        if set(tags).intersection({"LOC", "GPE"}):
            if len(label_tokens) == 2 and "," in cand_entity_title and len(entity_substr_split) == 1:
                if entity_substr_split[0] == label_tokens[1]:
                    if tags[0] == "COUNTRY":
                        substr_score = 0.0
                    else:
                        substr_score = 0.3
                else:
                    substr_score = 0.5
        else:
            if len(label_tokens) == 2 and len(entity_substr_split) == 1:
                if entity_substr_split[0] == label_tokens[0] and \
                        label_tokens[1].lower() in {"river", "lake", "mountain", "city", "town", "county"}:
                    substr_score = 1.0
                elif entity_substr_split[0] == label_tokens[1]:
                    if tags[0] == "COUNTRY":
                        substr_score = 0.0
                    else:
                        substr_score = 0.5
                elif entity_substr_split[0] == label_tokens[0]:
                    substr_score = 0.3
        if name_or_alias == "alias":
            substr_score *= 0.9
        return substr_score
    
    def make_objects_dicts(self, entity_tags_list, cand_ent_scores_list):
        entities_objects_list, entities_triplets_list, entities_for_ranking_list = [], [], []
        mention_objects_list, mention_objects_dict_list = [], []
        for tag, entities_scores in zip(entity_tags_list, cand_ent_scores_list):
            cur_objects_dict, cur_triplets_dict = {}, {}
            mention_objects, mention_objects_dict = set(), defaultdict(dict)
            entities_for_ranking = []
            if entities_scores:
                if self.conn_rank_mode == "max":
                    max_score = entities_scores[0][1][0]
                    for entity, scores in entities_scores:
                        if scores[0] == max_score:
                            entities_for_ranking.append(entity)
                else:
                    for entity, scores in entities_scores:
                        entities_for_ranking.append(entity)
                for entity, (substr_score, num_rels, page, descr, types, locations, types_of_sport, triplets_info,
                        ent_tag) in entities_scores:
                    objects, triplets = set(), set()
                    if isinstance(triplets_info, str):
                        rel_objects = triplets_info.split("---")
                        rel_objects = [elem.split() for elem in rel_objects]
                    else:
                        rel_objects = triplets_info
                    if isinstance(locations, str):
                        locations = locations.split()
                    for obj in locations:
                        objects.add(obj)
                        triplets.add(("P131", obj))
                        mention_objects.add(obj)
                        if "P131" in mention_objects_dict[obj]:
                            mention_objects_dict[obj]["P131"].append(entity)
                        else:
                            mention_objects_dict[obj]["P131"] = [entity]
                    if isinstance(types_of_sport, str):
                        types_of_sport = types_of_sport.split()
                    for obj in types_of_sport:
                        objects.add(obj)
                        triplets.add(("P641", obj))
                        mention_objects.add(obj)
                        if "P641" in mention_objects_dict[obj]:
                            mention_objects_dict[obj]["P641"].append(entity)
                        else:
                            mention_objects_dict[obj]["P641"] = [entity]
                    for rel_objects_elem in rel_objects:
                        if len(rel_objects_elem) > 1:
                            rel = rel_objects_elem[0]
                            cur_objects = rel_objects_elem[1:]
                            if rel not in {"P31", "P279", "P47", "P530", "P36"}:
                                for obj in cur_objects:
                                    objects.add(obj)
                                    triplets.add((rel, obj))
                                    mention_objects.add(obj)
                                    if rel in mention_objects_dict[obj]:
                                        mention_objects_dict[obj][rel].append(entity)
                                    else:
                                        mention_objects_dict[obj][rel] = [entity]
                    cur_objects_dict[entity] = objects
                    cur_triplets_dict[entity] = triplets
            entities_objects_list.append(cur_objects_dict)
            entities_triplets_list.append(cur_triplets_dict)
            mention_objects_list.append(mention_objects)
            mention_objects_dict_list.append(mention_objects_dict)
            entities_for_ranking_list.append(entities_for_ranking)
        return entities_objects_list, entities_triplets_list, mention_objects_list, mention_objects_dict_list, \
            entities_for_ranking_list
    
    def find_inters(self, cand_ent_scores_list, entity_tags_list, entity_sent_list, entities_sets_list,
                          entities_objects_list, entities_triplets_list, mention_objects_list,
                          mention_objects_dict_list, total_entities_scores_dict, entities_for_ranking_list):
        entities_conn_scores_list, entities_found_inters_list, entities_found_conn_list = [], [], []
        for entities_scores in cand_ent_scores_list:
            cur_entity_dict = {}
            for entity, scores in entities_scores:
                cur_entity_dict[entity] = 0
            entities_conn_scores_list.append(cur_entity_dict)
            cur_entity_dict = {}
            for entity, scores in entities_scores:
                cur_entity_dict[entity] = set()
            entities_found_inters_list.append(cur_entity_dict)
            found_conn = defaultdict(set)
            entities_found_conn_list.append(found_conn)

        for i in range(len(entities_for_ranking_list)):
            for entity1 in entities_for_ranking_list[i]:
                for j in range(len(entities_for_ranking_list)):
                    if i != j and not (entity_tags_list[i] in {"CITY", "COUNTY"} and entity_tags_list[j] == "EVENT"):
                        inters = entities_objects_list[i][entity1].intersection(entities_sets_list[j])
                        if inters:
                            for elem in inters:
                                if elem != entity1:
                                    entities_found_inters_list[i][entity1].add((elem, entity_tags_list[j], j,
                                                                                entity_sent_list[j]))
                                    entities_found_conn_list[i][(entity1, elem, entity_tags_list[j])].add(elem)
                                    entities_found_inters_list[j][elem].add((entity1, entity_tags_list[i], i,
                                                                             entity_sent_list[i]))
                                    entities_found_conn_list[j][(elem, entity1, entity_tags_list[i])].add(entity1)
                        else:
                            inters_len = 0
                            inters = set()
                            for rel1, obj1 in entities_triplets_list[i][entity1]:
                                if obj1 in mention_objects_list[j]:
                                    rels_and_obj2 = mention_objects_dict_list[j][obj1]
                                    for rel2 in rels_and_obj2:
                                        if (rel1 == rel2 and rel1 not in {"wiki_main_conn", "wiki_conn"}) or \
                                                (rel1 in {"wiki_main_conn", "wiki_conn"}
                                                 and rel2 not in {"wiki_main_conn", "wiki_conn"}) or \
                                                (rel2 in {"wiki_main_conn", "wiki_conn"}
                                                 and rel1 not in {"wiki_main_conn", "wiki_conn"}):
                                            entities2 = rels_and_obj2[rel2]
                                            if not rel1.startswith("wiki"):
                                                inters_rel = rel1
                                            else:
                                                inters_rel = rel2
                                            inters_entity = ""
                                            for entity2 in entities2:
                                                entity2_scores = total_entities_scores_dict.get(entity2, [100, 0.0, 0])
                                                if entity2_scores[0] == 0 and entity2_scores[1] >= 0.9:
                                                    inters_entity = entity2
                                                    break
                                            if inters_entity and inters_entity != entity1:
                                                inters_len += 1
                                                inters.add((inters_rel, obj1, inters_entity))
                                            else:
                                                for entity2 in entities2:
                                                    if entity2 != entity1:
                                                        inters_len += 1
                                                        inters.add((inters_rel, obj1, entity2))
                                                        break
                            for inters_rel, obj1, inters_entity in inters:
                                entities_found_inters_list[i][entity1].add(((inters_rel, obj1), entity_tags_list[j], j,
                                                                            entity_sent_list[j]))
                                entities_found_conn_list[i][(entity1, (inters_rel, obj1), entity_tags_list[j])].add(inters_entity)
                                entities_found_inters_list[j][inters_entity].add(((inters_rel, obj1),
                                                                                  entity_tags_list[j], i, entity_sent_list[i]))
                                entities_found_conn_list[j][(inters_entity, (inters_rel, obj1), entity_tags_list[j])].add(entity1)
        return entities_found_inters_list, entities_found_conn_list, entities_conn_scores_list
    
    def calc_inters_scores(self, entity_sent_list, entity_tags_list, entities_found_inters_list,
                                 entities_found_conn_list, total_entities_scores_dict, entities_triplets_list,
                                 entities_conn_scores_list):
        for i in range(len(entities_found_inters_list)):
            found_country = False
            for entity in entities_found_inters_list[i]:
                cnts_tag_dict = defaultdict(int)
                cnts_notag_dict = defaultdict(int)
                found_inters_list = []
                for elem, entity_tag, entity_ind, entity_sent_num in entities_found_inters_list[i][entity]:
                    if isinstance(elem, str):
                        found_inters_list.append([elem, entity_tag])
                
                found_inters_rel_dict, found_inters_proc_rel_dict = defaultdict(set), {}
                for elem, entity_tag, entity_ind, entity_sent_num in entities_found_inters_list[i][entity]:
                    if not isinstance(elem, str) and elem[0].startswith("P"):
                        found_inters_rel_dict[elem[0]].add((elem[1], entity_tag, entity_sent_num))
                
                for rel, obj_list in found_inters_rel_dict.items():
                    proc_obj_cnt_dict = {}
                    for cur_obj, entity_tag, entity_sent_num in obj_list:
                        if entity_sent_num == entity_sent_list[i]:
                            proc_obj_cnt_dict[cur_obj] = [entity_tag]
                    if proc_obj_cnt_dict:
                        for cur_obj, entity_tag, entity_sent_num in obj_list:
                            if cur_obj in proc_obj_cnt_dict and entity_sent_num != entity_sent_list[i]:
                                proc_obj_cnt_dict[cur_obj].append(entity_tag)
                    else:
                        for cur_obj, entity_tag, entity_sent_num in obj_list:
                            if cur_obj in proc_obj_cnt_dict:
                                proc_obj_cnt_dict[cur_obj].append(entity_tag)
                            else:
                                proc_obj_cnt_dict[cur_obj] = [entity_tag]
                    for cur_obj, entity_tags in proc_obj_cnt_dict.items():
                        for entity_tag in entity_tags:
                            found_inters_list.append([(rel, cur_obj), entity_tag])
                
                for elem, entity_tag, entity_ind, entity_sent_num in entities_found_inters_list[i][entity]:
                    if not isinstance(elem, str) and elem[0].startswith("wiki"):
                        found_inters_list.append([elem, entity_tag])
                high_conf_obj = ""
                incr = 0
                for elem, entity_tag in found_inters_list:
                    found_high_conf = False
                    for entity_inters in entities_found_conn_list[i][(entity, elem, entity_tag)]:
                        entity_inters_scores = total_entities_scores_dict.get(entity_inters, [100, 0.0, 0])
                        if entity_inters_scores[1] >= 0.9 and entity_inters_scores[0] == 0:
                            found_high_conf = True
                            break
                    if found_high_conf and (isinstance(elem, str) or elem[0] != "P17"):
                        if not isinstance(elem, str):
                            if elem[0] == "P641" and elem[1] == high_conf_obj:
                                incr = 25
                            elif elem[0] == "P276" or elem[1] == high_conf_obj:
                                incr = 10
                            elif elem[0] == "P17" and not found_country:
                                found_country = True
                                incr = 1
                            elif elem[0] != "P17":
                                incr = 1
                            high_conf_obj = elem[1]
                        else:
                            found_inters_rel = ""
                            for e_rel, e_obj in entities_triplets_list[i][entity]:
                                if e_rel == entity:
                                    found_inters_rel = e_rel
                                    break
                            if found_inters_rel == "P710":
                                incr = 50
                            elif found_inters_rel == "P276":
                                incr = 30
                            elif entity_tag not in {"CITY", "COUNTRY", "COUNTY", "LOC"}:
                                incr = 25
                            else:
                                incr = 15
                    else:
                        incr = 1
                    if entity_tag == entity_tags_list[i]:
                        cnts_tag_dict[elem] += incr
                    else:
                        cnts_notag_dict[elem] += incr
                
                cnts_tag_list = list(cnts_tag_dict.items())
                cnts_notag_list = list(cnts_notag_dict.items())
                
                entities_found_inters_list[i][entity] = (cnts_tag_list, cnts_notag_list)
                score_tag, score_notag = 0, 0
                for elem, cnt in cnts_tag_list:
                    if isinstance(elem, str):
                        score_tag += cnt * 3
                    else:
                        if elem[0] in {"P131", "P276"}:
                            if cnt > 4:
                                score_tag += cnt * 2
                            else:
                                score_tag += cnt
                        else:
                            score_tag += cnt
                for elem, cnt in cnts_notag_list:
                    if isinstance(elem, str):
                        score_notag += cnt * 6
                    else:
                        if elem[0] in {"P131", "P276"}:
                            if cnt > 4:
                                score_notag += cnt * 4
                            else:
                                score_notag += cnt * 2
                        else:
                            score_notag += cnt
                entities_conn_scores_list[i][entity] = (score_notag, score_tag)
        return entities_conn_scores_list, entities_found_inters_list
    
    def rank_by_connections(self, entity_substr_list: List[str],
                                  entity_tags_list: List[str],
                                  entity_sent_list: List[int],
                                  cand_ent_scores_list: List[List[Union[str, Tuple[str, str]]]],
                                  entities_scores_list: List[Dict[str, Tuple[float, float]]]):
        total_entities_scores_dict = {}
        for i in range(len(entities_scores_list)):
            for j, entity in enumerate(entities_scores_list[i]):
                prev_score = total_entities_scores_dict.get(entity, [100, 0.0, 0])
                cur_score = [j] + list(entities_scores_list[i][entity])
                if cur_score[1] >= prev_score[1]:
                    total_entities_scores_dict[entity] = cur_score
        
        entities_objects_list, entities_triplets_list, mention_objects_list, mention_objects_dict_list, \
            entities_for_ranking_list = self.make_objects_dicts(entity_tags_list, cand_ent_scores_list)
        
        entities_sets_list = []
        for entities_scores in cand_ent_scores_list:
            entities_sets_list.append({entity for entity, scores in entities_scores})
        
        entities_found_inters_list, entities_found_conn_list, entities_conn_scores_list = \
            self.find_inters(cand_ent_scores_list, entity_tags_list, entity_sent_list, entities_sets_list,
                             entities_objects_list, entities_triplets_list, mention_objects_list,
                             mention_objects_dict_list, total_entities_scores_dict, entities_for_ranking_list)
        
        entities_conn_scores_list, entities_found_inters_list = \
            self.calc_inters_scores(entity_sent_list, entity_tags_list, entities_found_inters_list,
                                    entities_found_conn_list, total_entities_scores_dict, entities_triplets_list,
                                    entities_conn_scores_list)
        
        entities_with_conn_scores_list = []
        for i in range(len(entities_conn_scores_list)):
            entities_with_conn_scores = []
            for entity in entities_conn_scores_list[i]:
                entity_type = entities_scores_list[i].get(entity, [0.0, 0, "", "", "", "", "", ""])[4]
                entity_triplets = entities_scores_list[i].get(entity, [0.0, 0, "", "", "", "", "", ""])[7]
                ent_tag = ""
                if entity_type == "Q5" and entity_triplets:
                    entity_triplets_list = entity_triplets.split("---")
                    entity_triplets_list = [tr.split() for tr in entity_triplets_list]
                    for rel, *objects in entity_triplets_list:
                        if rel == "P106" and objects:
                            occ = objects[0]
                            ent_tag = self.occ_labels_dict.get(occ, "")
                if not ent_tag:
                    ent_tag = entities_scores_list[i].get(entity, [""])[-1]
                if entity_type in {"Q3467906", "Q9135", "Q218616"}:
                    ent_tag = "product"
                
                cur_scores = [entity] + list(entities_scores_list[i].get(entity, [0.0, 0, "", "", ""]))[:5] + \
                    [ent_tag] + list(entities_conn_scores_list[i][entity])
                entities_with_conn_scores.append(cur_scores)
            entities_with_conn_scores = sorted(entities_with_conn_scores, key=lambda x: (x[7], x[8], x[1], x[2]),
                                               reverse=True)
            entities_with_conn_scores_list.append(entities_with_conn_scores)
            for entity in entities_conn_scores_list[i]:
                confs = list(entities_scores_list[i].get(entity, [0.0, 0, ""]))[:3]
                confs += list(entities_conn_scores_list[i][entity])
                entities_conn_scores_list[i][entity] = tuple(confs)
        
        return entities_with_conn_scores_list, entities_conn_scores_list

    def extract_additional_info(self, entity_ids_batch, wiki_types_batch):
        images_link_batch, categories_batch, first_par_batch, dbpedia_types_batch = [], [], [], []
        for entity_ids_list in entity_ids_batch:
            images_link_list, categories_list, first_par_list, dbpedia_types_list = [], [], [], []
            for entity_ids in entity_ids_list:
                images_links, categories, first_pars, dbpedia_types = [], [], [], []
                for entity_id in entity_ids:
                    if self.add_info_filename:
                        res = self.add_info_cur.execute(add_info_query, (entity_id,))
                    else:
                        res = self.cur.execute(add_info_query, (entity_id,))
                    entity_info = res.fetchall()
                    if entity_info:
                        images_links.append(entity_info[0][1])
                        categories.append(entity_info[0][2].split("\t"))
                        first_pars.append(entity_info[0][3])
                        cur_dbpedia_types = entity_info[0][4].split()
                        if "http://dbpedia.org/ontology/Person" in cur_dbpedia_types:
                            cur_dbpedia_types = [db_tp for db_tp in cur_dbpedia_types if db_tp not in
                                                 {"http://dbpedia.org/ontology/Animal",
                                                  "http://dbpedia.org/ontology/Eukaryote",
                                                  "http://dbpedia.org/ontology/Species"}]
                        dbpedia_types.append(cur_dbpedia_types)
                    else:
                        images_links.append("")
                        categories.append([])
                        first_pars.append("")
                        dbpedia_types.append([])
                images_link_list.append(images_links)
                categories_list.append(categories)
                first_par_list.append(first_pars)
                dbpedia_types_list.append(dbpedia_types)
            images_link_batch.append(images_link_list)
            categories_batch.append(categories_list)
            first_par_batch.append(first_par_list)
            dbpedia_types_batch.append(dbpedia_types_list)
        return images_link_batch, categories_batch, first_par_batch, dbpedia_types_batch

    def rank_by_description(
            self,
            entity_substr_list: List[str],
            entity_offsets_list: List[List[int]],
            cand_ent_list: List[List[str]],
            cand_ent_descr_list: List[List[str]],
            sentences_list: List[str],
            sentences_offsets_list: List[List[int]],
            substr_lens: List[int],
    ) -> Tuple[Union[List[List[str]], List[str]], Union[List[List[Any]], List[Any]]]:
        entity_ids_list = []
        conf_list = []
        contexts = []
        for (
                entity_substr,
                (entity_start_offset, entity_end_offset),
                candidate_entities,
        ) in zip(entity_substr_list, entity_offsets_list, cand_ent_list):
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
                context = (
                        sentence[start_of_sentence:rel_start_offset] + "[ent]" + sentence[
                                                                                 rel_end_offset:end_of_sentence]
                )
                if self.full_paragraph:
                    cur_sent_len = len(re.findall(self.re_tokenizer, context))
                    first_sentence_num = found_sentence_num
                    last_sentence_num = found_sentence_num
                    context = [context]
                    while True:
                        added = False
                        if last_sentence_num < len(sentences_list) - 1:
                            last_sentence_len = len(
                                re.findall(
                                    self.re_tokenizer,
                                    sentences_list[last_sentence_num + 1],
                                )
                            )
                            if cur_sent_len + last_sentence_len < self.max_paragraph_len:
                                context.append(sentences_list[last_sentence_num + 1])
                                cur_sent_len += last_sentence_len
                                last_sentence_num += 1
                                added = True
                        if first_sentence_num > 0:
                            first_sentence_len = len(
                                re.findall(
                                    self.re_tokenizer,
                                    sentences_list[first_sentence_num - 1],
                                )
                            )
                            if cur_sent_len + first_sentence_len < self.max_paragraph_len:
                                context = [sentences_list[first_sentence_num - 1]] + context
                                cur_sent_len += first_sentence_len
                                first_sentence_num -= 1
                                added = True
                        if not added:
                            break
                    context = " ".join(context)

            log.debug(f"rank, context: {context}")
            contexts.append(context)

        scores_list = self.entity_descr_ranker(contexts, cand_ent_list, cand_ent_descr_list)
        return scores_list
