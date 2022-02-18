import logging
import re
from typing import Callable, Any
import sentry_sdk
from os import getenv
import functools

from df_engine.core import Context, Actor
import df_engine.conditions as cnd

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


def is_sf(sf_name="Open.Give.Opinion"):
    def is_sf_handler(ctx: Context, actor: Actor, *args, **kwargs):
        try:
            last_utterance = (
                ctx.misc.get("agent", {})
                .get("dialog", {})
                .get("human_utterances", {})[-1]
            )
            utterance_sfcs = last_utterance.get("annotations", {}).get(
                "speech_function_classifier", []
            )
        except KeyError:
            utterance_sfcs = []

        return sf_name in utterance_sfcs

    return is_sf_handler


def is_ext_sf(ext_sf_name="React.Respond.Support.Reply.Agree"):
    def is_ext_sf_handler(ctx: Context, actor: Actor, *args, **kwargs):
        return ext_sf_name in ctx.misc.get("ext_sf", [[]])[-1]

    return is_ext_sf_handler


speech_functions = is_sf
