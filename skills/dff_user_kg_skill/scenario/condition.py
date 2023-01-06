import logging
import re
from typing import Callable
import sentry_sdk
from os import getenv
from df_engine.core import Context, Actor

import common.dff.integration.context as int_ctx
from common.universal_templates import if_lets_chat

sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def check_flag(prop: str) -> Callable:
    def check_flag_handler(ctx: Context, actor: Actor) -> bool:
        return ctx.misc.get("flags", {}).get(prop, False)

    return check_flag_handler


def skill_switch(ctx: Context, actor: Actor) -> bool:
    flag = False
    user_uttr = int_ctx.get_last_human_utterance(ctx, actor)
    if if_lets_chat(user_uttr["text"]) and re.findall(r"(\bpet|pets|hobby|hobbies)", user_uttr["text"]):
        flag = True
    return flag
