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
import itertools
import json
import os
import re
import multiprocessing as mp
import logging
from typing import List, Tuple, Dict, Any
import sentry_sdk

from hdt import HDTDocument

from common.wiki_skill import used_types as wiki_skill_used_types

sentry_sdk.init(os.getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
log = logging.getLogger(__name__)

prefixes = {
    "entity": "http://we",
    "label": "http://wl",
    "alias": "http://wal",
    "description": "http://wd",
    "rels": {"direct": "http://wpd", "no_type": "http://wp", "statement": "http://wps", "qualifier": "http://wpq"},
    "statement": "http://ws",
}
max_comb_num = 1e6

if os.getenv("LANGUAGE", "EN") == "RU":
    lang = "@ru"
else:
    lang = "@en"

FAST = int(os.getenv("FAST", "0"))

wiki_filename = "/root/.deeppavlov/downloads/wikidata/wikidata2022.hdt"
document = HDTDocument(wiki_filename)
USE_CACHE = True

ANIMALS_SKILL_TYPES = {"Q55983715", "Q16521", "Q43577", "Q39367", "Q38547"}

occ = {
    "business": [["Q131524", "enterpreneur"]],
    "sport": [
        ["Q937857", "football player"],
        ["Q2066131", "athlete"],
        ["Q3665646", "basketball player"],
        ["Q10833314", "tennis player"],
        ["Q19204627", "american football player"],
    ],
    "films": [
        ["Q10800557", "film actor"],
        ["Q33999", "actor"],
        ["Q10798782", "television actor"],
        ["Q2526255", "film director"],
    ],
    "music": [
        ["Q488205", "singer-songwriter"],
        ["Q36834", "composer"],
        ["Q177220", "singer"],
        ["Q753110", "songwriter"],
    ],
    "literature": [["Q49757", "poet"], ["Q6625963", "novelist"], ["Q214917", "playwright"], ["Q36180", "writer"]],
    "politics": [["Q82955", "politician"], ["Q372436", "statesperson"]],
}

top_n = 10


def find_top_people():
    top_people = {}

    for domain in occ:
        occupations = occ[domain]
        occ_people = []
        for elem, elem_label in occupations:
            tr, cnt = document.search_triples("", "http://wpd/P106", f"http://we/{elem}")
            for triplet in tr:
                occ_people.append(triplet[0])
        people_with_cnt = []
        for man in occ_people:
            tr, cnt = document.search_triples(f"{man}", "", "")
            people_with_cnt.append((man, cnt))
        people_with_cnt = sorted(people_with_cnt, key=lambda x: x[1], reverse=True)
        people_with_labels = []
        for man, counts in people_with_cnt[:top_n]:
            label = ""
            tr, cnt = document.search_triples(f"{man}", "http://wl", "")
            for triplet in tr:
                if triplet[2].endswith("@en"):
                    label = triplet[2].replace("@en", "").replace('"', "")
                    break
            if label:
                people_with_labels.append([man, label])

        top_people[domain] = people_with_labels

    for domain in occ:
        occupations = occ[domain]
        for elem, elem_label in occupations:
            occ_people = []
            tr, cnt = document.search_triples("", "http://wpd/P106", f"http://we/{elem}")
            for triplet in tr:
                occ_people.append(triplet[0])
            people_with_cnt = []
            for man in occ_people:
                tr, cnt = document.search_triples(f"{man}", "", "")
                people_with_cnt.append((man, cnt))
            people_with_cnt = sorted(people_with_cnt, key=lambda x: x[1], reverse=True)
            people_with_labels = []
            for man, counts in people_with_cnt[:top_n]:
                label = ""
                tr, cnt = document.search_triples(f"{man}", "http://wl", "")
                for triplet in tr:
                    if triplet[2].endswith("@en"):
                        label = triplet[2].replace("@en", "").replace('"', "")
                        break
                if label:
                    people_with_labels.append([man, label])

            top_people[elem_label] = people_with_labels

    return top_people


topic_skill_types = {
    "Q36180",  # writer
    "Q49757",  # poet
    "Q214917",  # playwright
    "Q1930187",  # journalist
    "Q6625963",  # novelist
    "Q28389",  # screenwriter
    "Q571",  # book
    "Q277759",  # book series
    "Q8261",  # novel
    "Q47461344",  # written work
    "Q7725634",  # literary work
    "Q1667921",  # novel series
    "Q33999",  # actor
    "Q177220",  # singer
    "Q17125263",  # youtuber
    "Q245068",  # comedian
    "Q947873",  # television presenter
    "Q10800557",  # film actor
    "Q10798782",  # television actor
    "Q2405480",  # voice actor
    "Q211236",  # celebrity
    "Q82955",  # politician
    "Q372436",  # statesperson
    "Q488205",  # singer-songwriter
    "Q36834",  # composer
    "Q177220",  # singer
    "Q753110",  # songwriter
    "Q134556",  # single
    "Q7366",  # song
    "Q482994",  # album
    "Q2066131",  # athlete
    "Q937857",  # football player
    "Q4009406",  # sprinter
    "Q10843402",  # swimmer
    "Q10873124",  # chess player
    "Q3665646",  # basketball player
    "Q10833314",  # tennis player
    "Q19204627",  # American football player
    "Q10871364",  # baseball player
    "Q20639856",  # team
    "Q847017",  # sports club
    "Q476028",  # football club
    "Q4498974",  # ice hockey team
    "Q570116",  # tourist attraction
    "Q11424",  # film
    "Q24856",  # film series
    "Q82955",  # politician
}


def search(self, query: List[str], unknown_elem_positions: List[Tuple[int, str]]) -> List[Dict[str, str]]:
    query = list(map(lambda elem: "" if elem.startswith("?") else elem, query))
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
    entity = entity.lstrip("+-")
    return entity


def find_label(entity: str, question: str) -> str:
    entity = str(entity).replace('"', "")
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
                found_label = (
                    label[2].strip(lang).replace('"', "").replace(".", " ").replace("$", " ").replace("  ", " ")
                )
                return found_label

    elif entity.endswith(lang):
        # entity: '"Lake Baikal"@en'
        entity = entity[:-3].replace(".", " ").replace("$", " ").replace("  ", " ")
        return entity

    elif "^^" in entity:
        """
        examples:
            '"1799-06-06T00:00:00Z"^^<http://www.w3.org/2001/XMLSchema#dateTime>' (date)
            '"+1642"^^<http://www.w3.org/2001/XMLSchema#decimal>' (number)
        """
        entity = entity.split("^^")[0]
        for token in ["T00:00:00Z", "+"]:
            entity = entity.replace(token, "")
        entity = format_date(entity, question).replace(".", "").replace("$", "")
        return entity

    elif entity.isdigit():
        entity = str(entity).replace(".", ",")
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


def find_entities_rels(entity1: str, entity2: str) -> List[str]:
    rels = []
    query = [f"{prefixes['entity']}/{entity1}", "", ""]
    triplets, c = document.search_triples(*query)
    for triplet in triplets:
        if triplet[2].split("/")[-1] == entity2:
            rels.append(triplet[1].split("/")[-1])
    query = [f"{prefixes['entity']}/{entity2}", "", ""]
    triplets, c = document.search_triples(*query)
    for triplet in triplets:
        if triplet[2].split("/")[-1] == entity1:
            rels.append(triplet[1].split("/")[-1])
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
            objects.extend([triplet[2].split("/")[-1] for triplet in triplets])
    else:
        triplets, cnt = document.search_triples("", rel, entity)
        if cnt < max_comb_num:
            objects.extend([triplet[0].split("/")[-1] for triplet in triplets])

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
    types = [triplet[2].split("/")[-1] for triplet in tr]
    if "Q5" in types:
        tr, c = document.search_triples(entity, f"{prefixes['rels']['direct']}/P106", "")
        types += [triplet[2].split("/")[-1] for triplet in tr]

    types = list(set(types))
    return types


def find_subclasses(entity: str):
    if not entity.startswith("http"):
        entity = f"{prefixes['entity']}/{entity}"
    tr, c = document.search_triples(entity, f"{prefixes['rels']['direct']}/P279", "")
    subclasses = [triplet[2].split("/")[-1] for triplet in tr]
    subclasses = list(set(subclasses))
    return subclasses


def find_types_2hop(entity: str):
    types_1hop = find_types(entity)
    types_2hop_list = []
    for tp in types_1hop:
        if tp != "Q5":
            types_2hop = find_types(tp) + find_subclasses(tp)
            types_2hop_list += types_2hop
    types_list = types_2hop_list + types_1hop
    types_list = list(set(types_list))
    return types_list


def find_objects_info(objects, num_objects=25):
    objects_info = []
    for obj in objects[:num_objects]:
        obj_label = find_label(obj, "")
        if obj_label and obj_label not in {"Not Found", "anonymous"}:
            objects_info.append((obj, obj_label))
    return sorted(objects_info)


def find_intersection(entity1, entity2, rel, direction):
    if direction == "backw":
        tr1, cnt1 = document.search_triples("", f"http://wpd/{rel}", f"http://we/{entity1}")
        tr2, cnt2 = document.search_triples("", f"http://wpd/{rel}", f"http://we/{entity2}")
        ind = 0
    else:
        tr1, cnt1 = document.search_triples(f"http://we/{entity1}", f"http://wpd/{rel}", "")
        tr2, cnt2 = document.search_triples(f"http://we/{entity2}", f"http://wpd/{rel}", "")
        ind = 2
    elem1 = set([triplet[ind] for triplet in tr1])
    elem2 = set([triplet[ind] for triplet in tr2])
    elements = elem1.intersection(elem2)
    info = []
    if elements:
        for elem in elements:
            label = find_label(elem, "")
            if label:
                info.append(label)
                break
    return info


def find_connection(person1, person2):
    rel_info = [
        ("P161", "films", "backw"),
        ("P175", "songs", "backw"),
        ("P50", "books", "backw"),
        ("P102", "party", "forw"),
        ("P54", "team", "forw"),
    ]
    entities1 = [(entity_id, n) for n, entity_id in enumerate(person1)]
    entities2 = [(entity_id, n) for n, entity_id in enumerate(person2)]
    entity_pairs = list(itertools.product(entities1, entities2))
    entity_pairs = sorted(entity_pairs, key=lambda x: sum([elem[1] for elem in x]))
    entity_pairs = [[elem[0] for elem in entity_pair] for entity_pair in entity_pairs]
    connection = ""
    info = []
    for entity1, entity2 in entity_pairs[:4]:
        info = []
        tr, cnt1 = document.search_triples(f"http://we/{entity1}", "http://wpd/P26", f"http://we/{entity2}")
        tr, cnt2 = document.search_triples(f"http://we/{entity2}", "http://wpd/P26", f"http://we/{entity1}")
        if cnt1 or cnt2:
            connection = "spouse"
            break
        tr, cnt1 = document.search_triples(f"http://we/{entity1}", "http://wpd/P451", f"http://we/{entity2}")
        tr, cnt2 = document.search_triples(f"http://we/{entity2}", "http://wpd/P451", f"http://we/{entity1}")
        if cnt1 or cnt2:
            connection = "partner"
            break
        for rel, conn, direction in rel_info:
            info = find_intersection(entity1, entity2, rel, direction)
            if info:
                connection = conn
                break
        if info:
            break
    return connection, info


def extract_info():
    art_genres = [
        ["film", "Q201658", "P136", ["Q11424"], "actor", "P161"],
        ["tv series", "Q15961987", "P136", ["Q5398426"], "tv actor", "P161"],
        ["song", "Q188451", "P136", ["Q134556", "Q7366"], "", ""],
        ["singer", "Q188451", "P136", ["Q488205", "Q36834", "Q177220", "Q753110"], "", ""],
        ["album", "Q188451", "P136", ["Q482994", "Q208569"], "", ""],
        ["book", "Q223393", "P136", ["Q7725634"], "writer", "P50"],
        ["athlete", "Q31629", "P641", ["Q5", "Q2066131"], "", ""],
        ["team", "Q31629", "P641", ["Q20639856", "Q12973014"], "", ""],
    ]
    art_genres_dict = {}
    people_genres_dict = {}
    banned_types = {"Q82955", "Q372436"}
    for art_type, genre_type, genre_rel, types, occupation, rel in art_genres:
        genres_list = find_object(genre_type, "P31", "backw")
        genre_labels_list = find_objects_info(genres_list, num_objects=200)
        genre_dict = {}
        people_dict = {}
        for genre, genre_label in genre_labels_list:
            art_objects = find_object(genre, genre_rel, "backw")
            filtered_art_objects = []
            for obj in art_objects:
                obj_types = find_types_2hop(obj)
                if set(types).intersection(obj_types) and not set(banned_types).intersection(obj_types):
                    filtered_art_objects.append(obj)
            art_objects = filtered_art_objects
            art_objects_with_scores = []

            delete_words = [" film", " music"]
            for word in delete_words:
                if genre_label.endswith(word):
                    length = len(word)
                    genre_label = genre_label[:-length]

            people_list = []
            for obj in art_objects:
                tr, cnt = document.search_triples(f"http://we/{obj}", "", "")
                art_objects_with_scores.append((obj, cnt))
                if occupation:
                    people = find_object(obj, rel, "forw")
                    people_list += people

            if occupation:
                people_with_scores = []
                for man in people_list:
                    tr, cnt = document.search_triples(f"http://we/{man}", "", "")
                    people_with_scores.append((man, cnt))
                people_with_scores = list(set(people_with_scores))
                people_with_scores = sorted(people_with_scores, key=lambda x: x[1], reverse=True)
                people_list = [man for man, score in people_with_scores]
                people_labels = find_objects_info(people_list[:15])
                if people_labels:
                    people_dict[genre_label] = people_labels

            art_objects_with_scores = sorted(art_objects_with_scores, key=lambda x: x[1], reverse=True)
            art_objects = [obj for obj, score in art_objects_with_scores]
            art_objects_labels = find_objects_info(art_objects[:15])

            if art_objects_labels:
                genre_dict[genre_label] = art_objects_labels
        art_genres_dict[art_type] = genre_dict
        if occupation:
            people_genres_dict[occupation] = people_dict
    return art_genres_dict, people_genres_dict


def find_top_triplets(entity, entity_substr, pos=None, token_conf=None, conf=None):
    triplets_info = {}
    if entity.startswith("Q"):
        triplets = {}
        entity_label = find_label(entity, "")
        triplets["plain_entity"] = entity
        for rel_id, rel_label in [
            ("P31", "instance of"),
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
            ("P800", "notable work"),
            ("P463", "musical group"),
            ("P1303", "instrument"),
            ("P166", "awards received"),
            ("P571", "inception"),
            ("P175", "performer"),
            ("P658", "tracklist"),
            ("P641", "sport"),
            ("P54", "member of sport team"),
            ("P1532", "country for sport"),
            ("P413", "position played on team"),
            ("P1344", "participant in"),
            ("P1449", "nickname"),
            ("P286", "head coach"),
            ("P118", "league"),
            ("P115", "home venue"),
            ("P2522", "victory"),
            ("P6364", "official color or colors"),
            ("P206", "located next to body of water"),
            ("P840", "narrative location"),
            ("P1830", "owner of"),
            ("P102", "member of political party"),
            ("P26", "spouse"),
            ("P451", "partner"),
        ]:
            objects = find_object(entity, rel_id, "")
            objects_info = find_objects_info(objects)
            if rel_label == "occupation":
                is_sportsman = any(
                    [{"Q2066131", "Q18536342"}.intersection(set(find_subclasses(occ))) for occ in objects]
                )
                if is_sportsman:
                    objects_info.append(["Q2066131", "athlete"])
            if objects_info:
                triplets[rel_label] = objects_info
        songs = find_object(entity, "P175", "backw")
        songs_with_labels = find_objects_info(songs)
        if songs_with_labels:
            triplets["songs of singer"] = songs_with_labels
        players = find_object(entity, "P54", "backw")
        players_with_labels = find_objects_info(players)
        if players_with_labels:
            triplets["players list"] = players_with_labels
        entity_types = set(find_types(entity) + find_subclasses(entity))
        if entity_types.intersection({"Q188451"}):  # music genre
            if entity_substr in genres_dict["singer"]:
                triplets["top singers"] = genres_dict["singer"][entity_substr]
            else:
                for genre in genres_dict["singer"]:
                    if genre in entity_substr or entity_substr in genre:
                        triplets["top singers"] = genres_dict["singer"][genre]
            if entity_substr in genres_dict["song"]:
                triplets["top songs"] = genres_dict["song"][entity_substr]
            else:
                for genre in genres_dict["song"]:
                    if genre in entity_substr or entity_substr in genre:
                        triplets["top songs"] = genres_dict["song"][genre]

        if entity_types.intersection({"Q31629", "Q4356073", "Q212434"}):  # type of sport
            if entity_substr in genres_dict["athlete"]:
                triplets["top athletes"] = genres_dict["athlete"][entity_substr]
            else:
                for sport in genres_dict["athlete"]:
                    if sport in entity_substr or entity_substr in sport:
                        triplets["top athletes"] = genres_dict["athlete"][sport]
            if entity_substr in genres_dict["team"]:
                triplets["top teams"] = genres_dict["team"][entity_substr]
            else:
                for sport in genres_dict["team"]:
                    if sport in entity_substr or entity_substr in sport:
                        triplets["top teams"] = genres_dict["team"][sport]

        triplets["entity_label"] = entity_label
        occupations = triplets.get("occupation", [])
        if occupations:
            occupation_titles = set([occ_title for occ_id, occ_title in occupations])
            if {"actor", "film actor", "television actor"}.intersection(occupation_titles):
                objects = find_object(entity, "P161", "backw")
                objects_info = find_objects_info(objects)
                if objects_info:
                    triplets["films of actor"] = objects_info
            if {"singer", "songwriter", "composer"}.intersection(occupation_titles):
                objects = find_object(entity, "P175", "backw")
                albums = [entity for entity in objects if "Q482994" in find_types(entity)]
                songs = [entity for entity in objects if "Q134556" in find_types(entity)]
                albums_info = find_objects_info(albums)
                if albums_info:
                    triplets["albums"] = albums_info
                songs_info = find_objects_info(songs)
                if songs_info:
                    triplets["songs"] = songs_info
        birth_date = find_object(entity, "P569", "")
        if birth_date:
            date_info = re.findall(r"([\d]{3,4})-([\d]{1,2})-([\d]{1,2})", birth_date[0])
            if date_info:
                year, month, day = date_info[0]
                age = datetime.datetime.now().year - int(year)
                triplets["age"] = age
        types_2hop = find_types_2hop(entity)
        types_2hop_with_labels = find_objects_info(types_2hop)
        triplets["types_2hop"] = types_2hop_with_labels
        if pos is not None:
            triplets["pos"] = pos
        if token_conf is not None:
            triplets["token_conf"] = token_conf
        if conf is not None:
            triplets["conf"] = conf
        if entity_substr.lower() in entity_label.lower():
            entity_substr = entity_label
        triplets_info[entity_substr] = triplets
    return triplets_info


def filter_by_types(objects, types):
    filtered_objects = []
    for obj in objects:
        found_types = find_types(obj)
        if set(found_types).intersection(types):
            filtered_objects.append(obj)
    return filtered_objects


def find_objects_by_category(what_to_find, category, subject):
    objects = []
    if category == "movie" and what_to_find == "actors":
        objects = find_object(subject, "P161", "forw")
    elif category == "show" and what_to_find == "actors":
        objects = find_object(subject, "P161", "forw")
    elif category == "show" and what_to_find == "episodes":
        objects = find_object(subject, "P179", "backw")
    elif category == "singer" and what_to_find == "songs":
        objects = find_object(subject, "P175", "backw")
        objects = filter_by_types(objects, {"Q134556", "Q7366"})
    elif category == "singer" and what_to_find == "albums":
        objects = find_object(subject, "P175", "backw")
        objects = filter_by_types(objects, {"Q482994", "Q208569"})
    elif category == "music" and what_to_find == "songs":
        objects = find_object(subject, "P175", "backw")
        objects = filter_by_types(objects, {"Q134556", "Q7366"})
    elif category == "music" and what_to_find == "albums":
        objects = find_object(subject, "P175", "backw")
        objects = filter_by_types(objects, {"Q482994", "Q208569"})
    elif category == "music" and what_to_find == "singers":
        objects = find_object(subject, "P175", "backw")
        objects = filter_by_types(objects, {"Q488205", "Q36834", "Q177220", "Q753110"})
    else:
        pass
    objects_with_labels = find_objects_info(objects[:20])
    return objects_with_labels


if USE_CACHE:
    with open("/root/.deeppavlov/downloads/wikidata/wikidata_cache.json", "r") as fl:
        wikidata_cache = json.load(fl)
    top_people = wikidata_cache["top_people"]
    genres_dict = wikidata_cache["genres_dict"]
    people_genres_dict = wikidata_cache["people_genres_dict"]
else:
    top_people = find_top_people()
    genres_dict, people_genres_dict = extract_info()

manager = mp.Manager()


def execute_queries_list(parser_info_list: List[str], queries_list: List[Any], utt_num: int):
    wiki_parser_output = []
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
            wiki_skill_triplets_info = {}
            animals_skill_triplets_info = {}
            try:
                for entity_info in query:
                    if entity_info:
                        entity_substr = entity_info.get("entity_substr", "")
                        entity_ids = entity_info.get("entity_ids", [])
                        tokens_match_conf_list = entity_info.get("tokens_match_conf", [1.0])
                        confidences = entity_info.get("confidences", [1.0])
                        if entity_ids:
                            entity_triplets_info = find_top_triplets(
                                entity_ids[0], entity_substr, 0, tokens_match_conf_list[0], confidences[0]
                            )
                            triplets_info = {**triplets_info, **entity_triplets_info}
                        found_topic_skills_info = False
                        found_wiki_skill_info = False
                        for n, (entity, token_conf, conf) in enumerate(
                            zip(entity_ids, tokens_match_conf_list, confidences)
                        ):
                            types = find_types(entity)
                            types_2hop = find_types_2hop(entity)
                            if not found_topic_skills_info and (
                                set(types).intersection(topic_skill_types)
                                or set(types_2hop).intersection(topic_skill_types)
                            ):
                                entity_triplets_info = find_top_triplets(entity, entity_substr, n, token_conf, conf)
                                topic_skills_triplets_info = {**topic_skills_triplets_info, **entity_triplets_info}
                                if not set(types_2hop).intersection({"Q11424", "Q24856"}):
                                    found_topic_skills_info = True
                            if not found_wiki_skill_info and (
                                set(types).intersection(wiki_skill_used_types)
                                or set(types_2hop).intersection(wiki_skill_used_types)
                            ):
                                entity_triplets_info = find_top_triplets(entity, entity_substr, n, token_conf, conf)
                                wiki_skill_triplets_info = {**wiki_skill_triplets_info, **entity_triplets_info}
                                if not set(types_2hop).intersection({"Q11424", "Q24856"}):
                                    found_wiki_skill_info = True
                            if found_topic_skills_info and found_wiki_skill_info:
                                break
                        for n, (entity, token_conf, conf) in enumerate(
                            zip(entity_ids, tokens_match_conf_list, confidences)
                        ):
                            types = find_types(entity)
                            types_2hop = find_types_2hop(entity)
                            if set(types).intersection(ANIMALS_SKILL_TYPES) or set(types_2hop).intersection(
                                ANIMALS_SKILL_TYPES
                            ):
                                entity_triplets_info = find_top_triplets(entity, entity_substr, n, token_conf, conf)
                                animals_skill_triplets_info = {**animals_skill_triplets_info, **entity_triplets_info}
            except Exception as e:
                log.info("Wrong arguments are passed to wiki_parser")
                sentry_sdk.capture_exception(e)
                log.exception(e)
            wiki_parser_output.append(
                {
                    "entities_info": triplets_info,
                    "topic_skill_entities_info": topic_skills_triplets_info,
                    "wiki_skill_entities_info": wiki_skill_triplets_info,
                    "animals_skill_entities_info": animals_skill_triplets_info,
                    "utt_num": utt_num,
                }
            )
        elif parser_info == "find_top_people":
            top_people_list = []
            try:
                for occ in query:
                    if occ in top_people:
                        top_people_list.append(top_people[occ])
            except Exception as e:
                log.info("Wrong arguments are passed to wiki_parser")
                sentry_sdk.capture_exception(e)
                log.exception(e)
            wiki_parser_output.append(top_people_list)
        elif parser_info == "find_entities_rels":
            rels = []
            try:
                rels = find_entities_rels(*query)
            except Exception as e:
                log.info("Wrong arguments are passed to wiki_parser")
                sentry_sdk.capture_exception(e)
                log.exception(e)
            wiki_parser_output.append(rels)
        elif parser_info == "find_connection":
            conn_info = []
            try:
                entities1, entities2 = query
                conn_info = list(find_connection(entities1, entities2))
            except Exception as e:
                log.info("Wrong arguments are passed to wiki_parser")
                sentry_sdk.capture_exception(e)
                log.exception(e)
            wiki_parser_output.append(conn_info)
        elif parser_info == "find_topic_info":
            objects = []
            try:
                if "genre" in query and "category" in query:
                    genre = query["genre"]
                    category = query["category"]
                    if category in {"actor", "singer", "tv actor", "writer"}:
                        if category in people_genres_dict and genre in people_genres_dict[category]:
                            objects = people_genres_dict[category][genre]
                    else:
                        if category in genres_dict and genre in genres_dict[category]:
                            objects = genres_dict[category][genre]
                elif "what_to_find" in query and "category" in query and "subject" in query:
                    what_to_find = query["what_to_find"]
                    category = query["category"]
                    subject = query["subject"]
                    objects = find_objects_by_category(what_to_find, category, subject)
                else:
                    log.debug("unsupported query type")
            except Exception as e:
                log.info("Wrong arguments are passed to wiki_parser")
                sentry_sdk.capture_exception(e)
                log.exception(e)
            wiki_parser_output.append(objects)
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
                triplets.extend(
                    [triplet for triplet in triplets_forw if not triplet[2].startswith(prefixes["statement"])]
                )
                triplets_backw, c = document.search_triples("", "", f"{prefixes['entity']}/{query}")
                triplets.extend(
                    [triplet for triplet in triplets_backw if not triplet[0].startswith(prefixes["statement"])]
                )
            except Exception as e:
                log.info("Wrong arguments are passed to wiki_parser")
                sentry_sdk.capture_exception(e)
                log.exception(e)
            wiki_parser_output.append(list(triplets))
        else:
            raise ValueError(f"Unsupported query type {parser_info}")
        return wiki_parser_output


def execute_queries_list_mp(parser_info_list: List[str], queries_list: List[Any], utt_num: int, wiki_parser_output):
    for elem in execute_queries_list_mp(parser_info_list, queries_list, utt_num):
        wiki_parser_output.append(elem)


def wp_call(parser_info_list: List[str], queries_list: List[Any], utt_num: int) -> List[Any]:
    if FAST:
        wiki_parser_output = execute_queries_list(parser_info_list, queries_list, utt_num)
    else:
        wiki_parser_output = manager.list()
        p = mp.Process(
            target=execute_queries_list_mp, args=(parser_info_list, queries_list, utt_num, wiki_parser_output)
        )
        p.start()
        p.join()
    log.info(f"wiki_parser_output: {wiki_parser_output}")
    return list(wiki_parser_output)
