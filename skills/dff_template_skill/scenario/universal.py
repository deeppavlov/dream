from typing import Optional, Tuple, Callable
import re
import logging
import json

from dff.core import Context, Actor

from tools.wiki import (
    get_name,
    what_is_book_about,
    get_published_year,
    best_plain_book_by_author,
    genre_of_book
)

logger = logging.getLogger(__name__)

BOOKREADS_DATA = json.load(open("bookreads_data.json", "r"))[0]
GENRE_DICT = {
    "memoir": re.compile(r"\bmemoir\b|\bautobiograph", re.IGNORECASE),
    "history biography": re.compile(r"\bbiograph", re.IGNORECASE),
    "science technology": re.compile(r"\btechnolog|\bscientific\b", re.IGNORECASE),
    "debut novel": re.compile(r"\bdebut\b", re.IGNORECASE),
    "graphic novels comics": re.compile(r"\bcomics\b|\bgraphic\b", re.IGNORECASE),
    "picture": re.compile(r"\bpicture\b", re.IGNORECASE),
    "romance": re.compile(r"\bromance\b|\bromantic\b|\blove\b", re.IGNORECASE),
    "non-fiction": re.compile(r"\bnonfiction\b|\bnon-fiction\b", re.IGNORECASE),
    "food cook": re.compile(r"\bfood\b|\bcook\b|\bkitchen\b", re.IGNORECASE),
    "poetry": re.compile(r"\bpoetry\b|\bpoesy\b|\bverse\b|\brhyme\b|\brime\b", re.IGNORECASE),
    "childrens": re.compile(r"\bchild\b|\bkids?\b", re.IGNORECASE),
    "mystery thriller": re.compile(r"\bmystery\b|\bthriller\b", re.IGNORECASE),
    "horror": re.compile(r"\bhorror\b", re.IGNORECASE),
    "humour": re.compile(r"\bhumor\b|\bfunny\b|\blaugh\b|\bcomics?\b", re.IGNORECASE),
    "fantasy": re.compile(r"\bfantasy\b", re.IGNORECASE),
    "science fiction": re.compile(r"\bsci-fi\b|\bscience fiction\b|\bspace\b", re.IGNORECASE),
    "historical fiction": re.compile(r"\bhistory\b|\bhistoric(al)?\b", re.IGNORECASE),
    "fiction": re.compile(r"\bfiction\b|\ball\b|\bany\b|\banything\b|everything", re.IGNORECASE),
}
GENRE_PATTERN = "|".join(GENRE_DICT.keys())
AUTHOR_PATTERN = re.compile(r"(?<=by )[A-Za-z][a-z]+( [A-Z][a-z]+){0,1}")

def get_slot(prop: str) -> Callable:
    """
    Use adapter to insert as a condition or a processing function
    Checks if a slot value is in place
    """
    def get_slot_handler(
        ctx: Context,
        actor: Actor
    ) -> Optional[str]:
        return ctx.misc.get("slots", {}).get(prop)
    
    return get_slot_handler


def get_book(
    ctx: Context,
    actor: Actor
) -> Optional[Tuple[str, Optional[str]]]:
    """
    Extract a book name from user request with wikiparser
    """
    annotated_utterance: dict = ctx.misc.get("agent", {}).get("dialog", {}).get("human_utterances", [{}])[-1]
    result = get_name(annotated_utterance, "book")
    if not result or not result[0]:
        return None
    return result


def get_movie(
    ctx: Context,
    actor: Actor
) -> Optional[Tuple[str, Optional[str]]]:
    """
    Extract a movie with wikiparser
    """
    annotated_utterance: dict = ctx.misc.get("agent", {}).get("dialog", {}).get("human_utterances", [{}])[-1]
    result = get_name(annotated_utterance, "movie")
    if not result or not result[0]:
        return None
    return result[0], result[2]


def get_genre_regexp(ctx: Context, actor: Actor) -> Optional[str]:
    """
    Extract the genre from user request if present
    Use adapter to insert as a condition or a processing function
    """
    last_request = ctx.last_request
    for key in GENRE_DICT.keys():
        if re.search(GENRE_DICT[key], last_request):
            return key
    return None


def get_book_genre(ctx: Context, actor: Actor) -> Optional[str]:
    """Extract the book genre from wiki"""
    book_plain = get_slot("cur_book_plain")(ctx, actor)
    return genre_of_book(book_plain)


def get_book_by_genre(ctx: Context, actor: Actor) -> Optional[Tuple[str, str]]:
    """
    Extract book, author, and description by genre from BOOKREADS
    """
    genre = get_slot("cur_genre")(ctx, actor)
    if not genre:
        return None
    used = ctx.misc.get(["used_phrases"], [])
    for book_info in BOOKREADS_DATA[genre]:
        book = book_info["book"]
        author = book_info["author"]
        description = book_info["description"]
        if not id(book) in used:
            used.append(id(book))
            ctx.misc["used_phrases"] = used
            logger.info(f"fetched {book}")
            return book, author, description
    return None


def about_bookreads(ctx: Context, actor: Actor) -> Optional[str]:
    bookname = get_slot("cur_book_name")(ctx, actor)
    reply = None
    logger.debug(f"Detected name {bookname} in last_bot_phrase")
    for genre in BOOKREADS_DATA:
        for book_ in BOOKREADS_DATA[genre]:
            if book_.get("title", "") == bookname:
                logger.debug(f"Returning phrase for book of genre {genre}")
                reply = book_.get("description")
                return reply
    return reply


def about_wiki(ctx: Context, actor: Actor) -> Optional[str]:
    plain_book = get_slot("cur_book_plain")(ctx, actor)
    return what_is_book_about(plain_book)


def get_author_regexp(ctx: Context, actor: Actor) -> Optional[str]:
    """
    Extract the author name from user request if present
    Use adapter to insert as a condition or a processing function
    """
    last_request = ctx.last_request
    author_candidate = re.search(AUTHOR_PATTERN, last_request)
    return None if not (x := author_candidate) else x.group()


def get_author(
    ctx: Context,
    actor: Actor
) -> Optional[Tuple[str, Optional[str], Optional[str]]]:
    """
    Extract the author name from user request with wikiparser
    """
    annotated_utterance: dict = ctx.misc.get("agent", {}).get("dialog", {}).get("human_utterances", [{}])[-1]
    result = get_name(annotated_utterance, "author")
    if not result or not result[0]:
        return None
    return result


def get_book_by_author(ctx: Context, actor: Actor) -> Optional[str]:
    """
    Find a bookname for a given author
    """
    author_plain = get_slot("cur_author_plain")(ctx, actor)
    prev_book = get_slot("cur_book_plain")(ctx, actor)
    return best_plain_book_by_author(
        plain_author_name=author_plain,
        plain_last_bookname=prev_book
    )


def get_book_year(ctx: Context, actor: Actor) -> Optional[str]:
    book_plain = get_slot("cur_book_plain")(ctx, actor)
    if not book_plain:
        return None
    return get_published_year(book_plain)