import logging
import re

from df_engine.core import Actor, Context
import common.dff.integration.context as int_ctx
from common.utils import yes_templates


logger = logging.getLogger(__name__)


def is_last_utt_approval_question(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    bot_uttr = int_ctx.get_last_bot_utterance(ctx, actor).get("text", "")
    if "Do you approve?" in bot_uttr:
        return True
    return False


def needs_details(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    shared_memory = int_ctx.get_shared_memory(ctx, actor)
    answer = shared_memory.get("needs_details", None)
    if answer and re.search(yes_templates, answer.lower()):
        return True
    return False
