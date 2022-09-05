import logging
import re
from . import response as loc_rsp
from common.personal_info import my_name_is_not_pattern
import common.dff.integration.context as int_ctx

from df_engine.core import Context, Actor

logger = logging.getLogger(__name__)


def wrong_name(ctx: Context, actor: Actor) -> bool:
    utt = int_ctx.get_last_human_utterance(ctx, actor)
    last_utt = utt["text"]
    if my_name_is_not_pattern.search(last_utt):
        return True
    return False
