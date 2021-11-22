import logging
import re
from typing import Callable, List, Optional, Union, Any
import sentry_sdk
from os import getenv
from datetime import datetime
import functools

from dff.core import Context, Actor
import dff.conditions as cnd

from common.universal_templates import NOT_LIKE_PATTERN, if_chat_about_particular_topic
from common.books import about_book, BOOK_PATTERN, book_skill_was_proposed
from common.dff.integration import condition as int_cnd
from common.universal_templates import if_chat_about_particular_topic
from common.utils import get_intents, get_topics, get_sentiment, is_yes, is_no

from scenario.processing import GENRE_PATTERN, CACHE

sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

USE_CACHE = True

SIDE_INTENTS = {
    "exit",
    "don't understand",
    "what_can_you_do",
    "what_is_your_job",
    "what_is_your_name",
    "what_time",
    "where_are_you_from",
    "who_made_you"    
}

FAVORITE_PATTERN = r"fav|favou{0,1}rite|preferred|loved|beloved|fondling|best|most interesting" # inherited from book utils + corrected
FAVORITE_PREDICATES = r"like|prefer|love|adore|enjoy"
CHRISTIANITY_PATTERN = r"(bibla\b|bible\b|bibel\b|scriptures\b|holy scripture\b|new testament\b)" # inherited from book utils + corrected
GENRE_SYNONYMS = r"(genre)|((kind|type|sort) of books)"
BOOK_SYNONYMS = r"book|piece of literature|literary piece"


def adapter(func: Callable) -> Callable:
    """
    Changes returned type to boolean
    """
    @functools.wraps(func)
    def adapter_wrapper(ctx: Context, actor: Actor) -> bool:
        result = func(ctx, actor)
        return bool(result)
    
    return adapter_wrapper


def annot_adapter(func: Callable) -> Callable:
    """
    Decorates Dream funcs that are fed annotated user utterances
    """
    @functools.wraps(func)
    def annot_wrapper(ctx: Context, actor: Actor) -> bool:
        result = func(ctx.misc["agent"]["dialog"]["human_utterances"][-1])
        return bool(result)
    
    return annot_wrapper


about_book = annot_adapter(about_book)

is_yes = annot_adapter(is_yes)

is_no = annot_adapter(is_no)


def sentiment_detected(name: str="positive", threshold: float=0.6) -> Callable:
    def sentiment_detected_handler(ctx: Context, actor: Actor) -> bool:
        sentiment_probs = get_sentiment(ctx.last_request, probs=True)
        return sentiment_probs.get(name, 0) >= threshold

    return sentiment_detected_handler


def check_flag(prop: str, default: bool) -> Callable:
    def check_flag_handler(
        ctx: Context,
        actor: Actor
    ) -> bool:
        return ctx.misc.get("history", {}).get(prop, default)
    
    return check_flag_handler


def check_unused(phrase: str) -> Callable:
    def check_used_handler(
        ctx: Context,
        actor: Actor
    ) -> bool:
        return id(phrase) not in ctx.misc.get("used_phrases", [])
    
    return check_used_handler


@functools.singledispatch
def is_last_used_phrase(phrase: Any) -> None:
    logger.debug(f"Incorrect data type {type(phrase)} in phrase check.")
    raise NotImplementedError(f"Incorrect data type {type(phrase)} in phrase check.")


@is_last_used_phrase.register
def _(phrase: str) -> Callable:
    def last_used_handler(ctx: Context, actor: Actor) -> bool:
        return (used := ctx.misc.get("used_phrases")) and used[-1] == id(phrase)
    
    return last_used_handler


@is_last_used_phrase.register
def _(phrase: List[str]) -> Callable:
    def last_used_handler(ctx: Context, actor: Actor) -> bool:
        return ((used := ctx.misc.get("used_phrases")) 
        and used[-1] in map(id, phrase))
    
    return last_used_handler


def start_condition(ctx: Context, actor: Actor) -> bool:
    return if_chat_about_particular_topic(
        ctx.misc["agent"]["dialog"]["human_utterances"][-1],
        ctx.misc["agent"]["dialog"]["bot_utterances"][-1],
        compiled_pattern=BOOK_PATTERN
    )

# annotated_utterance: Dict[str, str] = ctx.misc["agent"]["dialog"]["human_utterances"][-1]

def skill_proposed(ctx: Context, actor: Actor) -> bool:
    return book_skill_was_proposed(
        ctx.misc["agent"]["dialog"]["bot_utterances"][-1]
    )


def is_side_or_stop(ctx: Context, actor: Actor) -> bool:
    """Check for side intents (including exit)"""
    last_request = ctx.misc["agent"]["dialog"]["human_utterances"][-1]
    intents = set(get_intents(last_request, which="intent_catcher", probs=False))
    side_intent_present = len(intents.intersection(SIDE_INTENTS)) > 0
    return side_intent_present


def user_favorite_factory(subject: str) -> str:
    """Template for assertions about user preferences"""
    filled_template = rf"(my ({FAVORITE_PATTERN}) ({subject}) (is|are))|"
    rf"((['i]s|are) my ({FAVORITE_PATTERN}) ({subject}))|"
    rf"(the best)|"
    rf"(({subject}),{0,1} that i ({FAVORITE_PREDICATES})( the most)?)"
    return filled_template


def bot_favorite_factory(subject: str) -> str:
    """Template for questions about fav books, genres etc."""
    filled_template = rf"(^what['a-z ]+ your ({FAVORITE_PATTERN}) ({subject})\?{0,1}$)|"
    rf"(^(what|which)['a-z ]* ({subject}) [a-z ]+ ({FAVORITE_PATTERN}|{FAVORITE_PREDICATES}|most|recommend)\?{0,1}$)"
    return filled_template


# Where is it used
asked_what = cnd.regexp(
    re.compile(r"what (are|was|were|it|is)", re.IGNORECASE)
)

asked_to_offer_book = cnd.all(
    [
        int_cnd.is_question,
        cnd.regexp(re.compile(r"(suggest|recommend)", re.IGNORECASE))
    ]
)

asked_about_book = cnd.all(
    [
        int_cnd.is_question,
        about_book
    ]
)

asked_book_content = cnd.all(
    [
        int_cnd.is_question,
        cnd.regexp(re.compile(r"what('s| is).+ about\?{0,1}$", re.IGNORECASE))
    ]
)

asked_book_date = cnd.all(
    [
        int_cnd.is_question,
        cnd.regexp(
            re.compile(r"when [A-Za-z ]+ (out|written|published)\?{0,1}$", re.IGNORECASE)
        )
    ]
)

asked_fav_book = cnd.all(
    [
        int_cnd.is_question,
        cnd.regexp(
            re.compile(bot_favorite_factory(BOOK_SYNONYMS), re.IGNORECASE)
        )
    ]
)

asked_fav_genre = cnd.all(
    [
        int_cnd.is_question,
        cnd.regexp(
            re.compile(bot_favorite_factory(GENRE_SYNONYMS), re.IGNORECASE)
        )
    ]
)

asked_opinion_genre = cnd.all(
    [
        int_cnd.is_question,
        int_cnd.is_opinion_request,
        cnd.regexp(re.compile(GENRE_PATTERN, re.IGNORECASE)),
    ]
)

asked_opinion_book = cnd.all(
    [
        int_cnd.is_question,
        int_cnd.is_opinion_request,
        about_book,
    ]
)

asked_about_bible = cnd.regexp(re.compile(
    CHRISTIANITY_PATTERN, 
    re.IGNORECASE
))

told_fav_book = cnd.regexp(
    re.compile(user_favorite_factory(BOOK_SYNONYMS), re.IGNORECASE)
)

told_fav_genre = cnd.regexp(
    re.compile(user_favorite_factory(GENRE_SYNONYMS), re.IGNORECASE)
)

hasnt_read = cnd.regexp(re.compile(
    r"(not sure)|((haven'{0,1}t|have not|didn'{0,1}t|did not|never) (read|heard)?)",
    re.IGNORECASE
))

doesnt_know = cnd.regexp(re.compile(
    r"n['o]t (sure|know|remember|recall)|no (idea|clue)|never heard",
    re.IGNORECASE
))

# todo: add more phrases
likes_reading = cnd.regexp(re.compile(
    r"i (do )?(like|love|prefer|enjoy) (books{0,1}|read|to read|reading)", 
    re.IGNORECASE
))

dislikes_reading = cnd.any(
    [
        cnd.regexp(re.compile(
            rf"((n['o]t (want|like) (to )?(go on|continue|hear|talk|discuss|speak|listen))|"
            rf"(no more)|"
            rf"(whatever)|"
            rf"((stop|quit|exit)))", 
            re.IGNORECASE
        )),
        cnd.regexp(
            re.compile(NOT_LIKE_PATTERN, re.IGNORECASE)
        )
    ]
)

exit_skill = cnd.any(
    [
        is_side_or_stop,
        int_cnd.is_switch_topic,
        cnd.all([
            skill_proposed,
            int_cnd.is_no_vars
        ])
    ]
)