import logging
import re
from os import getenv

from df_engine.core import Actor, Context
import common.dff.integration.context as int_ctx


logger = logging.getLogger(__name__)


def is_last_utt_approval(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    # human_uttr = int_ctx.get_last_human_utterance(ctx, actor).get("text", "")
    bot_uttr = int_ctx.get_last_bot_utterance(ctx, actor).get("text", "")
    if "Do you approve?" in bot_uttr:
        return True
    return False

