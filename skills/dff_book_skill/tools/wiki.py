import re
import logging
import itertools
import random
import sentry_sdk
from typing import Dict, Tuple, Optional
from os import getenv
import pathlib
import _pickle as cPickle

from common.custom_requests import (
    request_entities_entitylinking,
    request_triples_wikidata,
)
from common.utils import entity_to_label, get_raw_entity_names_from_annotations

from scenario.response import CURRENT_YEAR

sentry_sdk.init(getenv("SENTRY_DSN"))
logger = logging.getLogger(__name__)

book_banned_words_file = pathlib.Path(__file__).parent / "book_banned_words.txt"
book_banned_words = {line.strip() for line in book_banned_words_file.read_text().split("\n") if line.strip()}
book_query_dict = cPickle.load(open("/global_data/book_query_dict.pkl", "rb"))


AUTHOR_WIKI_TYPES = ["Q36180", "Q18814623", "Q482980", "Q4853732", "Q6625963"]
BOOK_WIKI_TYPES = ["Q571", "Q7725634", "Q1667921", "Q277759", "Q8261", "Q47461344"]
MOVIE_WIKI_TYPES = ["Q11424", "Q24856", "Q202866"]


def is_wikidata_entity(entity: str) -> bool:
    """Assert that a string is a wikidata entity"""
    wrong_entity_format = entity and (entity[0] != "Q" or any([j not in "0123456789" for j in entity[1:]]))
    return not wrong_entity_format


def get_n_years(date: str) -> Optional[str]:
    """
    Turn the obtained publication date into a reply slot
    """
    if not isinstance(date, str):
        return None
    parsed_date = re.search(r"\d{4}", date)
    if not parsed_date:
        return None
    n_years = CURRENT_YEAR - int(parsed_date.group())
    if n_years == 0:
        return "Not so long "
    return f"{str(n_years)} years "


def get_name(
    annotated_phrase: dict,
    mode="author",
) -> Optional[Tuple[str, str, str]]:
    """
    Extract wiki entities of the specified type
    """
    plain_entity, found_entity, n_years_ago, attribute, film_director = (
        None,
        None,
        None,
        None,
        None,
    )
    try:
        all_found_entities = get_raw_entity_names_from_annotations(annotated_phrase.get("annotations", {}))
        if not all_found_entities:
            return None
        logger.info(f"Found entities in annotations {all_found_entities}")
        if mode == "author":
            types = AUTHOR_WIKI_TYPES
        elif mode == "book":
            types = BOOK_WIKI_TYPES
        elif mode == "movie":
            types = MOVIE_WIKI_TYPES
        else:
            raise Exception(f"Wrong mode: {mode}")
        n_years_ago = None
        wp_annotations = annotated_phrase.get("annotations", {}).get("wiki_parser", {})
        if isinstance(wp_annotations, list):
            wp_annotations = wp_annotations[0]
        toiterate_dict = wp_annotations.get("topic_skill_entities_info", {})
        for key in wp_annotations.get("entities_info", {}):
            if key not in toiterate_dict:
                toiterate_dict[key] = wp_annotations["entities_info"][key]
        keys = sorted(toiterate_dict, key=lambda x: -len(str(toiterate_dict[x])))
        #  logger.debug(toiterate_dict)
        #  To discern omonyms ( e.g serbian old king Stephen and Stephen King)
        #  we sort by the length of wikidata dict -
        # the more popular is the person the more info about it we have and the sooner we get it
        toiterate_dict = {key: toiterate_dict[key] for key in keys}
        for entity in toiterate_dict:
            found_types = []
            logger.debug(f"Examine {entity}")
            logger.debug(found_types)
            if "types_2hop" in toiterate_dict[entity]:
                found_types.extend([j[0] for j in toiterate_dict[entity]["types_2hop"] if j[0] not in found_types])
            logger.debug(found_types)
            if "instance of" in toiterate_dict[entity]:
                found_types.extend([j[0] for j in toiterate_dict[entity]["instance of"] if j[0] not in found_types])
            logger.debug(found_types)
            if not any([j in types for j in found_types]):
                logger.warning(f"Querying wikidata for {entity}")
                found_types = []
                for type_ in types:
                    request_answer = request_triples_wikidata(
                        "check_triplet",
                        [(entity, "P31", "forw")],
                        query_dict=book_query_dict,
                    )
                    if isinstance(request_answer, list) and request_answer[0]:
                        found_types.append(type_)
            logger.debug(f"Found types {found_types}")
            logger.debug(f"Interception {[k for k in types if k in found_types]}")
            if any([j in types for j in found_types]):
                logger.debug(f"{mode} found")
                found_entity = entity
                if "plain_entity" not in toiterate_dict[entity]:
                    logger.warning(f"No plain_entity found in annotation for {entity}")
                    plain_entities, _ = request_entities_entitylinking(entity, types=types, confidence_threshold=0.05)
                    plain_entity = plain_entities[0]
                else:
                    plain_entity = toiterate_dict[entity]["plain_entity"]
                if mode == "book":
                    if "publication date" in toiterate_dict[entity]:
                        publication_year = toiterate_dict[entity]["publication date"][0][0]
                    else:
                        logger.warning("No publication date found in annotation for {entity}")
                        publication_year = get_published_year(plain_entity)
                    n_years_ago = get_n_years(publication_year)
                elif mode == "movie":
                    if "film director" in toiterate_dict[entity]:
                        film_director = toiterate_dict[entity]["film producer"][0][0]
                    else:
                        film_director = get_author(plain_entity, mode="movie")
                elif mode == "author":  # to get rid of abbreviations such as J R R Tolkien
                    found_entity = " ".join([k for k in found_entity.split(" ") if len(k) > 1])
                    if "notable work" in toiterate_dict[entity]:
                        attribute = random.choice(toiterate_dict[entity]["notable work"])[1]
                break
            else:
                logger.info(f"No interception with {types}")
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
        return None
    entity = found_entity
    attribute = film_director if mode == "movie" else n_years_ago
    logger.info(f"Answer for get_name {entity} {attribute}")
    return entity, plain_entity, attribute


def get_published_year(book_entity: str) -> Optional[str]:
    """
    Extract the publication date
    """
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
            return None
    year_candidates = re.findall(r"[\d]{3,4}", published_year)
    if year_candidates:
        try:
            published_year: str = get_n_years(year_candidates[0])  # Changed to return a string
            assert published_year
        except Exception:
            # sentry_sdk.capture_exception(e)
            logger.exception(f"Could not obtain published year from {published_year_list}")
            return None
    logger.info(f"Answer for get_published_year {published_year}")
    return published_year


def author_genres(plain_author_name: str) -> list:
    plain_genres = request_triples_wikidata(
        "find_object", [(plain_author_name, "P136", "forw")], query_dict=book_query_dict
    )
    return list(map(entity_to_label, plain_genres))


def get_plain_genres(plain_bookname: str) -> list:
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


def get_author(plain_entity: str, return_plain=False, mode="book") -> Optional[str]:
    """
    Get the author for a plain book entity
    """
    logger.info(f"Calling get_author for {plain_entity}")
    logger.debug(f"Search author with entity {plain_entity.upper()}")
    if mode == "book":
        author_list = request_triples_wikidata(
            "find_object",
            [
                (plain_entity.upper(), "P50", "forw"),
                (plain_entity.upper(), "P800", "backw"),
            ],
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
    if is_wikidata_entity(author_entity):
        author_name = entity_to_label(author_entity)
        logger.info(f"Answer for get_author {author_name}")
        return author_name
    else:
        logger.warning(f"Wrong entity {author_entity}")
        return None


def parse_author_best_book(annotated_phrase: Dict[str, str], default_phrase=None) -> Tuple[str, Optional[str]]:
    """
    Get one book from the 'notable work' list
    """
    logger.debug(f'Calling parse_author_best_book for {annotated_phrase["text"]}')
    annotated_phrase["text"] = annotated_phrase["text"].lower()
    if re.search(r"\bis\b", annotated_phrase["text"]):
        annotated_phrase["text"] = annotated_phrase["text"].split(" is ")[1]
    _, plain_bookname, _ = get_name(annotated_phrase, "book", return_plain=True)
    if plain_bookname is None:
        logger.debug("Getting plain author")
        _, plain_author, _ = get_name(annotated_phrase, "author", return_plain=True)
    else:
        logger.debug(f"Processing bookname in get_author {plain_bookname}")
        plain_author = get_author(plain_bookname, return_plain=True, mode="book")
        logger.debug(f"Plain_author {plain_author}")
    if plain_author:
        logger.debug(f"author detected: {plain_author} bookname {plain_bookname}")
        plain_book = best_plain_book_by_author(
            plain_author_name=plain_author,
            plain_last_bookname=plain_bookname,
            default_phrase=default_phrase,
        )
        logger.debug(f"Answer for parse_author_best_book is {(plain_book, plain_author)}")
        return plain_book, plain_author
    logger.debug("No author found")
    return default_phrase, None


def get_booklist(plain_author_name: str) -> str:
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
    default_phrase: str = None,
    plain_last_bookname: Optional[str] = None,
    top_n_best_books: int = 1,
) -> Optional[str]:
    """
    Look up a book for an author
    """
    logger.debug(f"Calling best_plain_book_by_author for {plain_author_name} {plain_last_bookname}")
    default_phrase = "" if default_phrase is None else default_phrase
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


def what_is_book_about(book: Optional[str] = None) -> Optional[str]:
    """
    Fetch facts for a book
    """
    if not book:
        return None
    fact = None
    logger.info(f"Requesting for {book}")
    if is_wikidata_entity(book):
        plain_books = [book]
    else:
        plain_books, _ = request_entities_entitylinking(book, types=BOOK_WIKI_TYPES)
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
