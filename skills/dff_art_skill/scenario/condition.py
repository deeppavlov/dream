import logging
import re
from typing import Callable
import sentry_sdk
from os import getenv
from df_engine.core import Context, Actor

import common.dff.integration.context as int_ctx
from common.universal_templates import if_chat_about_particular_topic

sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

ART_PATTERN = re.compile(r"\b(art|drawing|painting)(\.|\b)", re.IGNORECASE)


def check_flag(prop: str) -> Callable:
    def check_flag_handler(ctx: Context, actor: Actor) -> bool:
        return ctx.misc.get("flags", {}).get(prop, False)

    return check_flag_handler


def art_skill_switch(ctx: Context, actor: Actor) -> bool:
    user_uttr = int_ctx.get_last_human_utterance(ctx, actor)
    bot_uttr = int_ctx.get_last_bot_utterance(ctx, actor)
    return if_chat_about_particular_topic(user_uttr, bot_uttr, compiled_pattern=ART_PATTERN)
