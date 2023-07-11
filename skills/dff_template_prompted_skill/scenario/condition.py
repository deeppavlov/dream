import logging
import re
from os import getenv

from df_engine.core import Actor, Context
import common.dff.integration.context as int_ctx


logger = logging.getLogger(__name__)
PROMPT_REPLACEMENT_COMMAND = re.compile(r"^/prompt")
PROMPT_RESET_COMMAND = re.compile(r"^/resetprompt")
ALLOW_PROMPT_RESET = int(getenv("ALLOW_PROMPT_RESET", 0))


def if_updating_prompt(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    human_uttr = int_ctx.get_last_human_utterance(ctx, actor).get("text", "")
    if ALLOW_PROMPT_RESET and re.search(PROMPT_REPLACEMENT_COMMAND, human_uttr):
        return True
    return False


def if_reseting_prompt(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    human_uttr = int_ctx.get_last_human_utterance(ctx, actor).get("text", "")
    if ALLOW_PROMPT_RESET and re.search(PROMPT_RESET_COMMAND, human_uttr):
        return True
    return False
