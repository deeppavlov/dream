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

import datetime
import os
import re
import multiprocessing as mp
import logging
from typing import List, Tuple, Dict, Any
import sentry_sdk

from hdt import HDTDocument

sentry_sdk.init(os.getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
log = logging.getLogger(__name__)

prefixes = {
    "entity": "http://we",
    "label": "http://wl",
    "alias": "http://wal",
    "description": "http://wd",
    "rels": {"direct": "http://wpd",
             "no_type": "http://wp",
             "statement": "http://wps",
             "qualifier": "http://wpq"
             },
    "statement": "http://ws"
}
max_comb_num = 1e6
lang = "@en"
wiki_filename = "/root/.deeppavlov/downloads/wikidata/wikidata_lite.hdt"
document = HDTDocument(wiki_filename)

topic_skill_types = set(["Q36180",  # writer
                         "Q49757",  # poet
                         "Q214917",  # playwright
                         "Q1930187",  # journalist
                         "Q6625963",  # novelist
                         "Q28389",  # screenwriter
                         "Q571",  # book
                         "Q7725634",  # literary work
                         "Q1667921",  # novel series
                         "Q33999",  # actor
                         "Q177220",  # singer
                         "Q17125263",  # youtuber
                         "Q245068",  # comedian
                         "Q2066131",  # sportsman
                         "Q947873",  # television presenter
                         "Q10800557",  # film actor
                         "Q10798782",  # television actor
                         "Q2405480",  # voice actor
                         "Q211236"  # celebrity
                         ])


def search(self, query: List[str], unknown_elem_positions: List[Tuple[int, str]]) -> List[Dict[str, str]]:
    query = list(map(lambda elem: "" if elem.startswith('?') else elem, query))
    subj, rel, obj = query
    combs = []
    triplets, cnt = document.search_triples(subj, rel, obj)
    if cnt < max_comb_num:
        if rel == prefixes["description"]:
            triplets = [triplet for triplet in triplets if triplet[2].endswith(lang)]
        combs = [{elem: triplet[pos] for pos, elem in unknown_elem_positions} for triplet in triplets]
    else:
        log.debug("max comb num exceeds")

    return combs


def format_date(entity, question):
    date_info = re.findall(r"([\d]{3,4})-([\d]{1,2})-([\d]{1,2})", entity)
    if date_info:
        year, month, day = date_info[0]
        if "how old" in question.lower():
            entity = datetime.datetime.now().year - int(year)
        elif day != "00":
            date = datetime.datetime.strptime(f"{year}-{month}-{day}", "%Y-%m-%d")
            entity = date.strftime("%d %B %Y")
        else:
            entity = year
        return entity
    entity = entity.lstrip('+-')
    return entity


def find_label(entity: str, question: str) -> str:
    entity = str(entity).replace('"', '')
    if entity.startswith("Q") or entity.startswith("P"):
        # example: "Q5513"
        entity = f"{prefixes['entity']}/{entity}"
        # "http://www.wikidata.org/entity/Q5513"

    if entity.startswith(prefixes["entity"]):
        labels, c = document.search_triples(entity, prefixes["label"], "")
        # labels = [["http://www.wikidata.org/entity/Q5513", "http://www.w3.org/2000/01/rdf-schema#label",
        #                                                    '"Lake Baikal"@en'], ...]
        for label in labels:
            if label[2].endswith(lang):
                found_label = label[2].strip(lang).replace('"', '').replace('.', ' ').replace('$', ' ').replace('  ',
                                                                                                                ' ')
                return found_label

    elif entity.endswith(lang):
        # entity: '"Lake Baikal"@en'
        entity = entity[:-3].replace('.', ' ').replace('$', ' ').replace('  ', ' ')
        return entity

    elif "^^" in entity:
        """
            examples:
                '"1799-06-06T00:00:00Z"^^<http://www.w3.org/2001/XMLSchema#dateTime>' (date)
                '"+1642"^^<http://www.w3.org/2001/XMLSchema#decimal>' (number)
        """
        entity = entity.split("^^")[0]
        for token in ["T00:00:00Z", "+"]:
            entity = entity.replace(token, '')
        entity = format_date(entity, question).replace('.', '').replace('$', '')
        return entity

    elif entity.isdigit():
        entity = str(entity).replace('.', ',')
        return entity

    return "Not Found"


def find_alias(entity: str) -> List[str]:
    aliases = []
    if entity.startswith(prefixes["entity"]):
        labels, cardinality = document.search_triples(entity, prefixes["alias"], "")
        aliases = [label[2].strip(lang).strip('"') for label in labels if label[2].endswith(lang)]
    return aliases


def find_rels(entity: str, direction: str, rel_type: str = "no_type", save: bool = False) -> List[str]:
    rels = []
    if not rel_type:
        rel_type = "direct"
    if direction == "forw":
        query = [f"{prefixes['entity']}/{entity}", "", ""]
    else:
        query = ["", "", f"{prefixes['entity']}/{entity}"]
    triplets, c = document.search_triples(*query)

    start_str = f"{prefixes['rels'][rel_type]}/P"
    rels = {triplet[1] for triplet in triplets if triplet[1].startswith(start_str)}
    rels = list(rels)
    return rels


def find_object(entity: str, rel: str, direction: str) -> List[str]:
    objects = []
    if not direction:
        direction = "forw"
    entity = f"{prefixes['entity']}/{entity.split('/')[-1]}"
    rel = f"{prefixes['rels']['direct']}/{rel}"
    if direction == "forw":
        triplets, cnt = document.search_triples(entity, rel, "")
        if cnt < max_comb_num:
            objects.extend([triplet[2].split('/')[-1] for triplet in triplets])
    else:
        triplets, cnt = document.search_triples("", rel, entity)
        if cnt < max_comb_num:
            objects.extend([triplet[0].split('/')[-1] for triplet in triplets])

    return objects


def check_triplet(subj: str, rel: str, obj: str) -> bool:
    subj = f"{prefixes['entity']}/{subj}"
    rel = f"{prefixes['rels']['direct']}/{rel}"
    obj = f"{prefixes['entity']}/{obj}"
    triplets, cnt = document.search_triples(subj, rel, obj)
    if cnt > 0:
        return True
    else:
        return False


def find_types(entity: str):
    types = []
    if not entity.startswith("http"):
        entity = f"{prefixes['entity']}/{entity}"
    tr, c = document.search_triples(entity, f"{prefixes['rels']['direct']}/P31", "")
    types = [triplet[2].split('/')[-1] for triplet in tr]
    if "Q5" in types:
        tr, c = document.search_triples(entity, f"{prefixes['rels']['direct']}/P106", "")
        types += [triplet[2].split('/')[-1] for triplet in tr]

    types = list(set(types))
    return types


def find_top_triplets(entity):
    triplets_info = {}
    if entity.startswith("Q"):
        triplets = {}
        entity_label = find_label(entity, "")
        for rel_id, rel_label in [("P31", "instance of"),
                                  ("P279", "subclass of"),
                                  ("P131", "located in"),
                                  ("P106", "occupation"),
                                  ("P361", "part of"),
                                  ("P17", "country"),
                                  ("P27", "country of sitizenship"),
                                  ("P569", "date of birth"),
                                  ("P1542", "has effect"),
                                  ("P580", "start time"),
                                  ("P1552", "has quality"),
                                  ("P50", "author"),
                                  ("P136", "genre"),
                                  ("P577", "publication date"),
                                  ("P800", "notable work")
                                  ]:
            objects = find_object(entity, rel_id, "")
            objects_info = []
            for obj in objects[:5]:
                obj_label = find_label(obj, "")
                if obj_label:
                    objects_info.append((obj, obj_label))
            if objects_info:
                triplets[rel_label] = objects_info
        triplets_info[entity_label] = triplets
    return triplets_info


manager = mp.Manager()


def execute_queries_list(parser_info_list: List[str], queries_list: List[Any], wiki_parser_output):
    for parser_info, query in zip(parser_info_list, queries_list):
        if parser_info == "find_rels":
            rels = []
            try:
                rels = find_rels(*query)
            except Exception as e:
                log.info("Wrong arguments are passed to wiki_parser")
                sentry_sdk.capture_exception(e)
                log.exception(e)
            wiki_parser_output += rels
        elif parser_info == "find_top_triplets":
            triplets_info = {}
            topic_skills_triplets_info = {}
            try:
                for entities in query:
                    if entities:
                        entity_triplets_info = find_top_triplets(entities[0])
                        triplets_info = {**triplets_info, **entity_triplets_info}
                    for entity in entities:
                        types = find_types(entity)
                        if set(types).intersection(topic_skill_types):
                            entity_triplets_info = find_top_triplets(entity)
                            topic_skills_triplets_info = {**topic_skills_triplets_info, **entity_triplets_info}
            except Exception as e:
                log.info("Wrong arguments are passed to wiki_parser")
                sentry_sdk.capture_exception(e)
                log.exception(e)
            wiki_parser_output.append({"entities_info": triplets_info,
                                       "topic_skill_entities_info": topic_skills_triplets_info})
        elif parser_info == "find_top_triplets_for_topic_skills":
            triplets_info = {}
            for entities_list in query:
                for entities in entities_list:
                    for entity in entities:
                        types = find_types(entity)
                        if set(types).intersection(topic_skill_types):
                            entity_triplets_info = find_top_triplets(entity)
                            triplets_info = {**triplets_info, **entity_triplets_info}
            wiki_parser_output.append(triplets_info)
        elif parser_info == "find_object":
            objects = []
            try:
                objects = find_object(*query)
            except Exception as e:
                log.info("Wrong arguments are passed to wiki_parser")
                sentry_sdk.capture_exception(e)
                log.exception(e)
            wiki_parser_output.append(objects)
        elif parser_info == "check_triplet":
            check_res = False
            try:
                check_res = check_triplet(*query)
            except Exception as e:
                log.info("Wrong arguments are passed to wiki_parser")
                sentry_sdk.capture_exception(e)
                log.exception(e)
            wiki_parser_output.append(check_res)
        elif parser_info == "find_label":
            label = ""
            try:
                label = find_label(*query)
            except Exception as e:
                log.info("Wrong arguments are passed to wiki_parser")
                sentry_sdk.capture_exception(e)
                log.exception(e)
            wiki_parser_output.append(label)
        elif parser_info == "find_types":
            types = []
            try:
                types = find_types(query)
            except Exception as e:
                log.info("Wrong arguments are passed to wiki_parser")
                sentry_sdk.capture_exception(e)
                log.exception(e)
            wiki_parser_output.append(types)
        elif parser_info == "find_triplets":
            triplets = []
            try:
                triplets_forw, c = document.search_triples(f"{prefixes['entity']}/{query}", "", "")
                triplets.extend([triplet for triplet in triplets_forw
                                 if not triplet[2].startswith(prefixes["statement"])])
                triplets_backw, c = document.search_triples("", "", f"{prefixes['entity']}/{query}")
                triplets.extend([triplet for triplet in triplets_backw
                                 if not triplet[0].startswith(prefixes["statement"])])
            except Exception as e:
                log.info("Wrong arguments are passed to wiki_parser")
                sentry_sdk.capture_exception(e)
                log.exception(e)
            wiki_parser_output.append(list(triplets))
        else:
            raise ValueError(f"Unsupported query type {parser_info}")


def wp_call(parser_info_list: List[str], queries_list: List[Any]) -> List[Any]:
    wiki_parser_output = manager.list()
    p = mp.Process(target=execute_queries_list, args=(parser_info_list, queries_list, wiki_parser_output))
    p.start()
    p.join()
    return list(wiki_parser_output)
