import re
import logging
import itertools
import random
import sentry_sdk
from typing import Any, Dict, Tuple, Set, Callable, Optional, Union
from os import getenv
import pathlib
import _pickle as cPickle
from functools import lru_cache

from dff.core import Context, Actor
from common.custom_requests import request_entities_entitylinking, request_triples_wikidata
from common.utils import get_entity_names_from_annotations, entity_to_label

from scenario.response import CURRENT_YEAR

sentry_sdk.init(getenv("SENTRY_DSN"))
logger = logging.getLogger(__name__)

book_banned_words_file = pathlib.Path(__file__).parent / "book_banned_words.txt"
book_banned_words = set([line.strip() for line in book_banned_words_file.read_text().split("\n") if line.strip()])
book_query_dict = cPickle.load(open("/global_data/book_query_dict.pkl", "rb"))


def process_movie(
    ent_label: str, 
    ent_plain: str, 
    ent_props: Dict[str, str]
) -> Tuple[str, Union[str, None]]:
    if "film director" in ent_props:
        film_director = ent_props["film director"][0][0]
    else:
        film_director = get_author(ent_plain, mode="movie")
    return ent_label, film_director


def process_author(
    ent_label: str, 
    ent_plain: str, 
    ent_props: Dict[str, str]
) -> Tuple[str, Union[str, None]]:
    ent_label = " ".join(
        [word for word in ent_label.split(" ") if len(word) > 1]
    )
    notable_work = ent_props.get("notable_work") # in many cases best books are fetched with the author entity
    if not notable_work:
        return ent_label, None
    return ent_label, random.choice(notable_work)[0]


def process_book(
    ent_label: str, 
    ent_plain: str, 
    ent_props: Dict[str, str]
) -> Tuple[str, Optional[str]]:
    if "publication date" in ent_props:
        publication_year = ent_props["publication date"][0][0]
    else:
        logger.warning("No publication date found")
        publication_year = get_published_year(ent_plain)
    return ent_label, get_n_years(publication_year)


def get_n_years(date: str) -> Optional[str]:
    "Turn the obtained publication date into a reply slot"
    if type(date) != str:
        return None
    parsed_date = re.search(r"\d{4}", date)
    if not parsed_date:
        return None
    n_years = int(parsed_date.group()) - CURRENT_YEAR
    if n_years == 0:
        return "Not so long "
    return f"{str(n_years)} years "


WIKI_MAPPING: Dict[str, Dict[str, Union[Callable, Set[str]]]] = {
    "author":{
        "types": {"Q214917", "Q36180", "Q18844224", "Q18814623", "Q482980", "Q4853732", "Q6625963"},
        "processing":process_author
    },
    "book":{
        "types": {"Q571", "Q7725634", "Q1667921", "Q277759", "Q8261", "Q47461344"},
        "processing":process_book
    },
    "movie":{
        "types": {"Q11424", "Q24856", "Q202866"},
        "processing":process_movie
    }
}


def is_wikidata_entity(entity: str) -> bool:
    wrong_entity_format = entity and (entity[0] != "Q" or any([j not in "0123456789" for j in entity[1:]]))
    return not wrong_entity_format


@lru_cache(maxsize=1)
def get_sorted_entities(annotated_utterance: Dict[str, str]) -> Optional[Dict[str, Dict[str, str]]]:
    """Get a sorted list of entities from wikidata annotations"""
    found_entities = get_entity_names_from_annotations(annotated_utterance)
    if not found_entities:
        logger.warning(f'Entities not found in {annotated_utterance["annotations"].get("entity_linking", {})}')
        return None
    wikiparser_annot = annotated_utterance["annotations"].get("wiki_parser", {})
    if isinstance(wikiparser_annot, list):
        wikiparser_annot = wikiparser_annot[0]
    entities = {
        **wikiparser_annot.get("entities_info", {}),
        **wikiparser_annot.get("topic_skill_entities_info", {}), 
    }
    #  sorting so that more relevant entities come first
    keys = sorted(entities.keys(), key=lambda x: -len(str(entities[x])))
    entities = {x: entities[x] for x in keys}
    return entities


def get_name(
    ctx: Context,
    mode: str,
) -> Optional[Tuple[Optional[str], Optional[str]]]:
    """Get an entity of the specified type from the last user request"""
    annotated_utterance: Dict[str, str] = ctx.misc["agent"]["dialog"]["human_utterances"][-1]
    entities = get_sorted_entities(annotated_utterance)
    if not entities or len(entities) == 0:
        return None
    for entity in entities.items():
        result_tuple = entity_processing(entity, mode)
        if result_tuple:
            break
    return result_tuple


def entity_processing(
    entity: Tuple[str, Dict[str, str]],
    mode: str,
) -> Optional[Tuple[str, str, str]]:
    """Get specified information from a single entity"""
    target_types = WIKI_MAPPING[mode]["types"]
    ent_label, ent_props = entity
    found_types = set([
        *ent_props.get("types_2hop", []),
        *ent_props.get("instance_of", [])
    ])
    logger.debug(f"Found types: {found_types}")
    found_types = target_types.intersection(found_types)
    if not found_types:
        for _type in target_types:
            request_answer = request_triples_wikidata(
                "check_triplet",
                [(ent_label, "P31", "forw")],
                query_dict=book_query_dict
            )
            if isinstance(request_answer, list) and request_answer[0]:
                found_types.add(_type)
        logger.debug(f"Found types {found_types}")
    if len(found_types) == 0:
        logger.info(f"No intersection with {target_types}")
        return None        
    logger.debug(f"{mode} found")
    ent_plain = label_to_entity(ent_label, ent_props, target_types)
    processing = WIKI_MAPPING[mode]["processing"]
    ent_label, attribute = processing(ent_label, ent_plain, ent_props)
    return ent_label, ent_plain, attribute


def label_to_entity(
    ent_label: str,
    ent_props: Dict[str, str],
    types: Optional[Set[str]]=None
) -> str:
    """Obtain a plain entity name from its label"""
    if not types:
        types = {}
    if "plain_entity" not in ent_props:
        plain_entities, _ = request_entities_entitylinking(
            ent_label, types=types, confidence_threshold=0.05
        )
        return plain_entities[0].strip()
    return ent_props["plain_entity"].strip()


def get_published_year(book_entity: str) -> Optional[str]:
    assert is_wikidata_entity(book_entity)
    book_entity = book_entity.strip()
    published_year = None
    published_year_list = request_triples_wikidata(
        "find_object", [(book_entity, "P577", "forw")], query_dict=book_query_dict
    )
    logger.info(f"Received {published_year_list}")
    if isinstance(published_year_list, str):
        published_year = published_year_list
    else:
        while published_year_list and type(published_year_list[0]) == list:
            # Support different formats of wikiparser output
            published_year_list = published_year_list[0]
        if published_year_list and type(published_year_list[0]) == str:
            published_year = published_year_list[0]
        else:
            published_year = ""
    year_candidates = re.findall(r"[\d]{3,4}", published_year)
    if year_candidates:
        try:
            published_year: str = get_n_years(year_candidates[0]) # Changed to return a string
            assert published_year
        except Exception:
            # sentry_sdk.capture_exception(e)
            logger.exception(f"Could not obtain published year from {published_year_list}")
            return None
    logger.info(f"Answer for get_published_year {published_year}")
    return published_year


def author_genres(plain_author_name):
    plain_genres = request_triples_wikidata(
        "find_object", [(plain_author_name, "P136", "forw")], query_dict=book_query_dict
    )
    return list(map(entity_to_label, plain_genres))


def get_plain_genres(plain_bookname: str):
    plain_genres = request_triples_wikidata(
        "find_object", [(plain_bookname, "P136", "forw")], query_dict=book_query_dict
    )
    MAX_DEPTH = 5
    for _ in range(MAX_DEPTH):
        if plain_genres and isinstance(plain_genres[0], list):
            plain_genres = plain_genres[0]
    logger.debug(f"Plain_genres {plain_genres}")
    return plain_genres


def genre_of_book(plain_bookname: str) -> Optional[str]:
    logger.info(f"Call genre_of_book for {plain_bookname}")
    plain_genres = get_plain_genres(plain_bookname)
    if plain_genres:
        plain_genres = sorted(plain_genres, key=lambda x: int(x[1:]))
        genre = entity_to_label(plain_genres[0])
        if genre[0] not in ["aeoi"]:
            genre = f"a {genre}"
        else:
            genre = f"an {genre}"
        return genre
    else:
        return None


def get_author(plain_entity, return_plain=False, mode="book"):
    # Input bookname output author name
    logger.info(f"Calling get_author for {plain_entity}")
    logger.debug(f"Search author with entity {plain_entity.upper()}")
    if mode == "book":
        author_list = request_triples_wikidata(
            "find_object",
            [(plain_entity.upper(), "P50", "forw"), (plain_entity.upper(), "P800", "backw")],
            query_dict=book_query_dict,
        )
    else:
        author_list = request_triples_wikidata("find_object", [(plain_entity.upper(), "P57", "forw")], query_dict={})
    logger.info(f"Author list received {author_list}")
    author_list = list(itertools.chain.from_iterable(author_list))
    author_list = list(set(author_list))
    author_list = [x[x.find("Q") :] for x in author_list]  # to unify representations
    sorted_author_list = sorted(author_list, key=lambda x: int(x[1:]))  # Sort entities by frequency
    if not sorted_author_list:
        return None
    author_entity = sorted_author_list[0]
    if return_plain:
        logger.info(f"Answer {author_entity}")
        return author_entity
    else:
        if is_wikidata_entity(author_entity):
            author_name = entity_to_label(author_entity)
            logger.info(f"Answer for get_author {author_name}")
            return author_name
        else:
            logger.warning(f"Wrong entity {author_entity}")
            return None


def parse_author_best_book(annotated_phrase, default_phrase=None):
    logger.debug(f'Calling parse_author_best_book for {annotated_phrase["text"]}')
    annotated_phrase["text"] = annotated_phrase["text"].lower()
    if re.search(r"\bis\b", annotated_phrase["text"]):
        annotated_phrase["text"] = annotated_phrase["text"].split(" is ")[1]
    plain_bookname, _ = get_name(annotated_phrase, "book", return_plain=True)
    if plain_bookname is None:
        logger.debug(f"Getting plain author")
        plain_author, _ = get_name(annotated_phrase, "author", return_plain=True)
    else:
        logger.debug(f"Processing bookname in get_author {plain_bookname}")
        plain_author = get_author(plain_bookname, return_plain=True, mode="book")
        logger.debug(f"Plain_author {plain_author}")
    if plain_author:
        logger.debug(f"author detected: {plain_author} bookname {plain_bookname}")
        plain_book = best_plain_book_by_author(
            plain_author_name=plain_author, plain_last_bookname=plain_bookname, default_phrase=default_phrase
        )
        logger.debug(f"Answer for parse_author_best_book is {(plain_book, plain_author)}")
        return plain_book, plain_author
    else:
        logger.debug("No author found")
        return default_phrase, None


def get_booklist(plain_author_name):
    book_list = request_triples_wikidata(
        "find_object",
        [(plain_author_name, "P800", "forw"), (plain_author_name, "P50", "backw")],
        query_dict=book_query_dict,
    )
    book_list = list(itertools.chain.from_iterable(book_list))
    book_list = list(set(book_list))
    book_list = [x[x.find("Q") :] for x in book_list if x]  # to unify representations
    book_list = sorted(book_list, key=lambda x: int(x[1:]))
    return book_list


def best_plain_book_by_author(
    plain_author_name: str, 
    default_phrase: str,
    plain_last_bookname: Optional[str] = None,
    top_n_best_books: int = 1
) -> Optional[str]:
    """Given an author, look one of his books up"""
    logger.debug(f"Calling best_plain_book_by_author for {plain_author_name} {plain_last_bookname}")
    # best books
    last_bookname = "NO_BOOK"
    try:
        book_list = get_booklist(plain_author_name)
        if plain_last_bookname is not None:
            book_list = [j for j in book_list if plain_last_bookname not in j]
            last_bookname = entity_to_label(plain_last_bookname)
        logger.debug("List of returned books - processed")
        logger.debug(book_list)
        best_bookname = default_phrase  # default value
        if book_list:
            filtered_bookname_list = []
            for book in book_list:
                logger.debug(f"{last_bookname.lower()} {entity_to_label(book).lower()}")
                if len(filtered_bookname_list) < top_n_best_books:
                    if last_bookname.lower() not in entity_to_label(book).lower():
                        filtered_bookname_list.append(book)
                        if len(filtered_bookname_list) >= top_n_best_books:
                            break
            if len(filtered_bookname_list) > 0:
                best_bookname = random.choice(filtered_bookname_list)
        logger.debug(f"Answer for best_plain_book_by_author {best_bookname}")
        return best_bookname
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(f"Error processing {book_list}")
        return default_phrase

def what_is_book_about(book: str) -> Optional[str]:
    fact = None
    logger.info(f"Requesting for {book}")
    if is_wikidata_entity(book):
        plain_books = [book]
    else:
        plain_books, _ = request_entities_entitylinking(book, types=WIKI_MAPPING["book"]["types"])
        logger.info(f"After request {plain_books}")
    if plain_books:
        plain_book = plain_books[0]
        subjects = request_triples_wikidata("find_object", [(plain_book, "P921", "forw")], query_dict={})[0]
        if subjects:
            fact = f"The main subject of this book is {entity_to_label(subjects[0])}."
        locations = request_triples_wikidata("find_object", [(plain_book, "P840", "forw")], query_dict={})[0]
        if len(locations) > 1:
            fact = f"{fact} Apart from other locations,"
        if locations:
            fact = f"{fact} The action of this book takes place in {entity_to_label(locations[0])}."
        if not subjects or not locations:
            characters = request_triples_wikidata("find_object", [(plain_book, "P674", "forw")], query_dict={})[0]
            if characters:
                fact = f"{fact} One of the main characters of this book is {entity_to_label(characters[0])}."
    logger.info(f"Final fact {fact}")
    return fact