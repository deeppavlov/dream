import logging
import re
from typing import Callable, Any
import sentry_sdk
from os import getenv
import functools

from dff.core import Context, Actor
import dff.conditions as cnd

from common.books import about_book, BOOK_PATTERN, book_skill_was_proposed
from common.dff.integration import condition as int_cnd
from common.universal_templates import (
    NOT_LIKE_PATTERN,
    if_chat_about_particular_topic,
    is_switch_topic,
    tell_me_more,
)
from common.utils import (
    get_intents,
    get_sentiment,
    is_question,
    is_opinion_request,
    is_opinion_expression,
)  # present in integration

import scenario.response as loc_rsp
import scenario.universal as universal
from scenario.universal import GENRE_PATTERN, get_slot

sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
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
    "who_made_you",
}

FAVORITE_PATTERN = r"fav|favou{0,1}rite|preferred|loved|beloved|fondling|best|most interesting"  # inherited from book utils + corrected
FAVORITE_PREDICATES = r"like|prefer|love|adore|enjoy"
CHRISTIANITY_PATTERN = r"(bibla\b|bible\b|bibel\b|scriptures\b|holy scripture\b|new testament\b)"  # inherited from book utils + corrected
GENRE_SYNONYMS = r"(genre)|((kind|type|sort) of books)"
BOOK_SYNONYMS = r"book|piece of literature|literary piece"


def to_boolean(func: Callable) -> Callable:
    """
    Changes returned type to boolean
    """

    @functools.wraps(func)
    def adapter_wrapper(ctx: Context, actor: Actor) -> bool:
        if ctx.validation:
            return False
        result = func(ctx, actor)
        return bool(result)

    return adapter_wrapper


def annot_utt_adapter(func: Callable) -> Callable:
    """
    Decorates Dream funcs that are fed annotated user utterances
    """

    @functools.wraps(func)
    def annot_wrapper(ctx: Context, actor: Actor) -> bool:
        if ctx.validation:
            return False
        result = func(
            ctx.misc.get("agent", {}).get("dialog", {}).get("human_utterances", [{}])[-1]
        )
        return bool(result)

    return annot_wrapper


about_book = annot_utt_adapter(about_book)

is_question = annot_utt_adapter(is_question)

is_opinion_request = annot_utt_adapter(is_opinion_request)

is_opinion_expression = annot_utt_adapter(is_opinion_expression)

is_switch_topic = annot_utt_adapter(is_switch_topic)

tell_me_more = annot_utt_adapter(tell_me_more)


def sentiment_detected(name: str = "positive", threshold: float = 0.6) -> Callable:
    def sentiment_detected_handler(ctx: Context, actor: Actor) -> bool:
        if ctx.validation:
            return False
        last_request = (
            ctx.misc.get("agent", {}).get("dialog", {}).get("human_utterances", [{}])[-1]
        )
        sentiment_probs = get_sentiment(last_request, probs=True)
        return sentiment_probs.get(name, 0) >= threshold

    return sentiment_detected_handler


def check_flag(prop: str) -> Callable:
    def check_flag_handler(ctx: Context, actor: Actor) -> bool:
        return ctx.misc.get("flags", {}).get(prop, False)

    return check_flag_handler


def check_unused(phrase: str) -> Callable:
    def check_used_handler(ctx: Context, actor: Actor) -> bool:
        return id(phrase) not in ctx.misc.get("used_phrases", [])

    return check_used_handler


@functools.singledispatch
def is_last_used_phrase(phrase: Any) -> None:
    logger.debug(f"Incorrect data type {type(phrase)} in phrase check.")
    raise NotImplementedError(f"Incorrect data type {type(phrase)} in phrase check.")


@is_last_used_phrase.register
def _(phrase: str) -> Callable:
    def last_used_handler(ctx: Context, actor: Actor) -> bool:
        if ctx.validation:
            return False
        last_response = ctx.last_response
        return phrase in last_response
        # return (used := ctx.misc.get("used_phrases", False)) and used[-1] == id(phrase)

    return last_used_handler


@is_last_used_phrase.register
def _(phrase: list) -> Callable:
    def last_used_handler(ctx: Context, actor: Actor) -> bool:
        if ctx.validation: 
            return False
        last_response = ctx.last_response
        return any([item in last_response for item in phrase])
        # return (used := ctx.misc.get("used_phrases", False)) and used[-1] in map(
        #     id, phrase
        # )

    return last_used_handler


def start_condition(ctx: Context, actor: Actor) -> bool:
    return if_chat_about_particular_topic(
        ctx.misc.get("agent", {}).get("dialog", {}).get("human_utterances", [{}])[-1],
        ctx.misc.get("agent", {}).get("dialog", {}).get("bot_utterances", [{}])[-1],
        compiled_pattern=BOOK_PATTERN,
    )


def is_proposed_skill(ctx: Context, actor: Actor) -> bool:
    return book_skill_was_proposed(
        ctx.misc.get("agent", {}).get("dialog", {}).get("bot_utterances", [{}])[-1]
    )


def genrebook_request_detected(ctx: Context, actor: Actor) -> bool:
    """Reimplementation of the original function"""
    asked_fav = is_last_used_phrase(loc_rsp.WHAT_GENRE_FAV)(ctx, actor)
    agreed_to_recommend = (is_last_used_phrase(loc_rsp.GENRE_ADVICE_PHRASE)(ctx, actor) 
    and int_cnd.is_yes_vars(ctx, actor))
    asked_to_recommend = asked_to_offer_book(ctx, actor)
    genre_in_phrase = check_genre_regexp(ctx, actor)
    return any([asked_fav, agreed_to_recommend, asked_to_recommend]) and genre_in_phrase


def is_side_or_stop(ctx: Context, actor: Actor) -> bool:
    """
    Check for side intents (including exit)
    """
    last_request = (
        ctx.misc.get("agent", {}).get("dialog", {}).get("human_utterances", [{}])[-1]
    )
    intents = set(get_intents(last_request, which="intent_catcher", probs=False))
    side_intent_present = len(intents.intersection(SIDE_INTENTS)) > 0
    logger.debug("Side intent detected, exiting")
    return side_intent_present


def no_entities(ctx: Context, actor: Actor) -> bool:
    """
    Assert that no entities were recognized in the previous utterance
    """
    last_request = (
        ctx.misc.get("agent", {}).get("dialog", {}).get("human_utterances", [{}])[-1]
    )
    return bool(last_request.get("annotations", {}).get("ner"))


def user_favorite_factory(subject: str) -> str:
    """
    Template for assertions about user preferences
    """
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


def book_in_request(ctx: Context, actor: Actor) -> bool:
    return bool(
        universal.get_book(ctx, actor)
    )


def genrebook_in_slots(ctx: Context, actor: Actor) -> bool:
    return bool(check_slot("cur_genre") and universal.get_book_by_genre(ctx, actor))


def author_in_request(ctx: Context, actor: Actor) -> bool:
    return bool(universal.get_author(ctx, actor))


def about_in_slots(ctx: Context, actor: Actor) -> bool:
    return bool(
        (check_slot("cur_book_plain") and universal.about_wiki(ctx, actor))
        or (check_slot("cur_book_name") and universal.about_bookreads(ctx, actor))
    )


def about_in_request(ctx: Context, actor: Actor) -> bool:
    return bool(
        (book := universal.get_book(ctx, actor))
        and universal.what_is_book_about(book[1])
    )


def bestbook_in_request(ctx: Context, actor: Actor) -> bool:
    return bool(
        (author := universal.get_author(ctx, actor))
        and (author[2]
        or universal.best_plain_book_by_author(author[1]))
    )


def date_in_slots(ctx: Context, actor: Actor) -> bool:
    return bool(
        (book := universal.get_book(ctx, actor))
        and (book[2] 
        or check_slot("cur_book_ago"))
    )


def date_in_request(ctx: Context, actor: Actor) -> bool:
    return bool(
        (book := universal.get_book(ctx, actor))
        and universal.get_published_year(book[1])
    )


def genre_in_request(ctx: Context, actor: Actor) -> bool:
    return bool(
        (book := universal.get_book(ctx, actor)) and universal.genre_of_book(book[1])
    )


def genre_in_slots(ctx: Context, actor: Actor) -> bool:
    return bool(
        (book_plain := get_slot("cur_book_plain")(ctx, actor)) 
        and universal.genre_of_book(book_plain)
    ) 


def movie_in_request(ctx: Context, actor: Actor) -> bool:
    return bool(universal.get_movie(ctx, actor))


def check_slot(prop: str) -> bool:
    return to_boolean(
        universal.get_slot(prop)
    )


check_author_regexp: Callable[[Context, Actor], bool] = to_boolean(
    universal.get_author_regexp
)

check_genre_regexp: Callable[[Context, Actor], bool] = to_boolean(
    universal.get_genre_regexp
)

asked_what = cnd.regexp(re.compile(r"what (are|was|were|it|is)", re.IGNORECASE))

asked_to_offer_book = cnd.all(
    [
        # int_cnd.is_question,
        is_question,
        cnd.regexp(re.compile(r"(suggest|recommend)", re.IGNORECASE)),
    ]
)

asked_about_book = cnd.all(
    [
        # int_cnd.is_question,
        is_question,
        about_book,
    ]
)

asked_book_content = cnd.all(
    [
        # int_cnd.is_question,
        is_question,
        cnd.regexp(re.compile(r"what('s| is).+ about\?{0,1}$", re.IGNORECASE)),
    ]
)

asked_book_date = cnd.all(
    [
        # int_cnd.is_question,
        is_question,
        cnd.regexp(
            re.compile(
                r"when [A-Za-z ]+ (\bout\b|\bwritten\b|\bpublished\b)\?{0,1}$",
                re.IGNORECASE,
            )
        ),
    ]
)

asked_fav_book = cnd.all(
    [
        # int_cnd.is_question,
        is_question,
        cnd.regexp(re.compile(bot_favorite_factory(BOOK_SYNONYMS), re.IGNORECASE)),
    ]
)

asked_fav_genre = cnd.all(
    [
        # int_cnd.is_question,
        is_question,
        cnd.regexp(re.compile(bot_favorite_factory(GENRE_SYNONYMS), re.IGNORECASE)),
    ]
)

asked_opinion_genre = cnd.all(
    [
        # int_cnd.is_question,
        is_question,
        # int_cnd.is_opinion_request,
        is_opinion_request,
        cnd.regexp(re.compile(GENRE_PATTERN, re.IGNORECASE)),
    ]
)

asked_opinion_book = cnd.all(
    [
        # int_cnd.is_question,
        is_question,
        # int_cnd.is_opinion_request,
        is_opinion_request,
        about_book,
    ]
)

asked_about_bible = cnd.regexp(re.compile(CHRISTIANITY_PATTERN, re.IGNORECASE))

told_fav_book = cnd.regexp(
    re.compile(user_favorite_factory(BOOK_SYNONYMS), re.IGNORECASE)
)

told_fav_genre = cnd.regexp(
    re.compile(user_favorite_factory(GENRE_SYNONYMS), re.IGNORECASE)
)

hasnt_read = cnd.regexp(
    re.compile(
        r"(not sure)|((haven'{0,1}t|have not|didn'{0,1}t|did not|never) (read|heard)?)",
        re.IGNORECASE,
    )
)

doesnt_know = cnd.regexp(
    re.compile(
        r"n['o]t (sure|know|remember|recall)|no (idea|clue)|never heard", re.IGNORECASE
    )
)

# todo: add more phrases
likes_reading = cnd.regexp(
    re.compile(
        r"i (do )?(like|love|prefer|enjoy) (books{0,1}|read|to read|reading)",
        re.IGNORECASE,
    )
)

dislikes_reading = cnd.any(
    [
        cnd.regexp(
            re.compile(
                rf"((n['o]t (want|like) (to )?(go on|continue|hear|talk|discuss|speak|listen))|"
                rf"(no more)|"
                rf"(whatever)|"
                rf"((stop|quit|exit)))",
                re.IGNORECASE,
            )
        ),
        cnd.regexp(re.compile(NOT_LIKE_PATTERN)),
    ]
)

exit_skill = cnd.any(
    [
        is_side_or_stop,
        # int_cnd.is_switch_topic,
        # is_switch_topic,
        cnd.all([is_proposed_skill, int_cnd.is_no_vars]),
    ]
)

has_read_transitions = {
    ("concrete_book_flow", "ask_opinion", 2): int_cnd.is_yes_vars,
    ("genre_flow", "not_read_genrebook", 1.9): cnd.any([int_cnd.is_no_vars, hasnt_read]),
    ("genre_flow", "genrebook_info", 1.8): cnd.all(
        [about_in_slots, tell_me_more]
    ),
    ("undetected_flow", "change_branch", 1.7): cnd.true()  
}