import functools
import logging
import random
from typing import (
    Any, 
    Callable, 
    List, 
    Tuple, 
    Optional, 
    Dict, 
    Union, 
    Iterable,
    Iterator
)
import re
import json

from common.dff.integration.processing import save_slots_to_ctx
from dff.core import Context, Actor
from dff.caching import OneTurnCache
from dff.core.keywords import TRANSITIONS, RESPONSE
from tools.wiki import (
    get_name,
    what_is_book_about,
    get_published_year,
    best_plain_book_by_author,
    genre_of_book
)
from scenario.response import WHAT_BOOK_IMPRESSED_MOST, FAVOURITE_BOOK_PHRASES, WHAT_GENRE_FAV

logger = logging.getLogger(__name__)

BOOKREADS_DATA = json.load(open("bookreads_data.json", "r"))[0]

CACHE = OneTurnCache()

AUTHOR_PATTERN = re.compile(r"(?<=by )[A-Za-z][a-z]+( [A-Z][a-z]+){0,1}")

GENRE_DICT:Dict[str, Union[str, re.Pattern]] = {
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


def adapter(func: Callable) -> Callable:
    """
    Changes the returned value to a Context object, 
    while `save_to_slots` processes the initial value
    """
    @functools.wraps(func)
    def adapter_wrapper(ctx: Context, actor: Actor) -> Context:
        func(ctx, actor)
        return ctx
    
    return adapter_wrapper


@functools.singledispatch
def save_to_slots(slots: Any) -> None:
    """A decorator for saving to slots. Ignores `NoneType`."""
    raise NotImplementedError


@save_to_slots.register
def _(slots: str) -> Callable:
    def slot_decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def slot_wrapper(ctx: Context, actor: Actor) -> Optional[str]:
            result = func(ctx, actor)
            if result is None:
                return result
            ctx.misc["slots"] = ctx.misc.get("slots", {})
            ctx.misc["slots"].update({slots: result})
            return result
        
        return slot_wrapper

    return slot_decorator


@save_to_slots.register
def _(slots: Tuple[str]) -> Callable:
    def slot_decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def slot_wrapper(ctx: Context, actor: Actor) -> Iterable[str]:
            results = func(ctx, actor)
            if results is None:
                return results
            ctx.misc["slots"] = ctx.misc.get("slots", {})
            ctx.misc["slots"].update( 
                **{
                    slot: result for slot, result in zip(slots, results)
                    if result is not None
                }
            )
            return results
        
        return slot_wrapper

    return slot_decorator


def save_random_subdict(keys: Iterator, maindict: Dict) -> Callable:
    try:
        return save_slots_to_ctx({**maindict[next(keys)]})
    except StopIteration:
        return save_slots_to_ctx(
            {
                **maindict[random.choice(list(maindict.keys()))]
            }
        )


def set_flag(label: str, value: Union[str, bool]) -> Callable:
    """Sets a flag, modified coronavirus skill"""
    def set_flag_handler(ctx: Context, actor: Actor) -> Context:
        ctx.misc["history"] = ctx.misc.get("history", {})
        ctx.misc["history"].update({label : value})
        return ctx

    return set_flag_handler


def add_to_used(value: str):
    """Temporary solution is to keep the history in the form of ids instead of strings"""
    def used_handler(ctx: Context, actor: Actor) -> Context:
        if ["used_phrases"] not in ctx.misc:
            ctx.misc["used_phrases"] = []
        ctx.misc["used_phrases"].append(id(value))
        return ctx

    return used_handler


def get_slot(prop: str) -> Callable:
    """
    Use adapter to insert as a condition or a processing function
    Checks if a slot value is in place
    """
    def check_slot_handler(
        ctx: Context,
        actor: Actor
    ) -> Optional[str]:
        return ctx.misc.get("slots", {}).get(prop)
    
    return check_slot_handler


@save_to_slots("cur_genre")
@CACHE.cache
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


@save_to_slots("cur_genre")
@CACHE.cache
def get_book_genre(ctx: Context, actor: Actor) -> Optional[str]:
    """Extract the book genre from wiki"""
    book_plain = get_slot("cur_book_plain")(ctx, actor)
    return genre_of_book(book_plain)


@save_to_slots(("cur_book_name", "cur_book_author", "cur_book_about"))
@CACHE.cache
def get_book_by_genre(ctx: Context, actor: Actor) -> Optional[Tuple[str, str]]:
    """
    Extract book, author, and description by genre from BOOKREADS
    """
    genre = get_slot("cur_genre")(ctx, actor)
    if not genre:
        return None
    for book_info in BOOKREADS_DATA[genre]:
        book = book_info["book"]
        author = book_info["author"]
        description = book_info["description"]
        if not id(book) in ctx.misc["used_phrases"]:
            ctx.misc["used_phrases"].append(id(book))
            return book, author, description
    return None


@save_to_slots("cur_author_best")
@CACHE.cache
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


@save_to_slots("cur_book_about")
@CACHE.cache
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


@save_to_slots("cur_book_about")
@CACHE.cache
def about_wiki(ctx: Context, actor: Actor) -> Optional[str]:
    plain_book = get_slot("cur_book_plain")(ctx, actor)
    return what_is_book_about(plain_book)


@save_to_slots("cur_book_author")
@CACHE.cache
def get_author_regexp(ctx: Context, actor: Actor) -> Optional[str]:
    """
    Extract the author name from user request if present
    Use adapter to insert as a condition or a processing function
    """
    last_request = ctx.last_request
    author_candidate = re.search(AUTHOR_PATTERN, last_request)
    return None if not (x := author_candidate) else x.group()


@save_to_slots(("cur_book_author", "cur_author_plain", "cur_author_best"))
@CACHE.cache
def get_author(
    ctx: Context,
    actor: Actor
) -> Optional[Tuple[str, Optional[str], Optional[str]]]:
    result = get_name(ctx, "author")
    if not result or not result[0]:
        return None
    return result


@save_to_slots(("cur_book_name", "cur_book_plain", "cur_book_ago"))
@CACHE.cache
def get_book(
    ctx: Context,
    actor: Actor
) -> Optional[Tuple[str, Optional[str]]]:
    result = get_name(ctx, "book")
    if not result or not result[0]:
        return None
    return result


@save_to_slots(("cur_book_movie", "cur_book_director"))
@CACHE.cache
def get_movie(
    ctx: Context,
    actor: Actor
) -> Optional[Tuple[str, Optional[str]]]:
    result = get_name(ctx, "movie")
    if not result or not result[0]:
        return None
    return result[0], result[2]


@save_to_slots("cur_book_ago")
@CACHE.cache
def get_book_year(ctx: Context, actor: Actor) -> Optional[str]:
    book_plain = get_slot("cur_book_plain")(ctx, actor)
    if not book_plain:
        return None
    return get_published_year(book_plain)


def interrupt(ctx: Context, actor: Actor) -> Context:
    """
    Override transitions and exit the skill
    """
    label = ctx.last_label
    actor.plot[label[0]][label[1]].transitions = {
        ("global_flow", "fallback", 2): lambda ctx, actor: True
    }
    return ctx


def append_unused(phrases: List[str], exit_on_exhaust: bool=False):
    """
    Add a postfix from a list, modified coronavirus skill
    Can exit the skill on exhaust
    """
    def append_unused_phrase_handler(
        ctx: Context,
        actor: Actor,
    ) -> Context:
        node = ctx.a_s.get("processed_node", ctx.a_s["next_node"])
        used: List[int] = ctx.misc.get("used_phrases")
        confidences: List[float] = [1] * len(phrases)

        for idx, phrase in enumerate(phrases):
            times: int = used.count(phrase) # coerced to False if 0
            if times == 0:
                ctx = add_to_used(phrase)(ctx, actor)
                node.response = f"{node.response} {phrase}"
                ctx.a_s["processed_node"] = node
                return ctx
            confidences[idx] *= 0.4 ** times
        
        if exit_on_exhaust:
            return interrupt(ctx, actor)
        
        idx = confidences.index(max(confidences))
        ctx = add_to_used(phrases[idx])(ctx, actor)
        node.response = f"{node.response} {phrases[idx]}"
        ctx.a_s["processed_node"] = node
        return ctx

    return append_unused_phrase_handler


def append_question(ctx: Context, actor: Actor) -> Context:
    """
    Implements the original booklink2reply intended to change the branch
    Exits the skill if no questions remain
    """
    questions: List[str] = [WHAT_BOOK_IMPRESSED_MOST]
    if not ctx.misc.get("history").get("denied_favorite", False):
        questions.extend(FAVOURITE_BOOK_PHRASES)
    if not ctx.misc.get("history").get("user_fav_genre_visited", False):
        questions.append(WHAT_GENRE_FAV)
    ctx = append_unused(questions, exit_on_exhaust=True)(ctx, actor)
    return ctx