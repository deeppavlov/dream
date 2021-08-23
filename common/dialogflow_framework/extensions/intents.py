import logging
from dff import Context, Actor
import common.dialogflow_framework.utils.state as state_utils
from common.utils import is_yes, is_no, is_donot_know
from common.dialogflow_framework.extensions.facts_utils import provide_facts_request

logger = logging.getLogger(__name__)


def yes_intent(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    vars = ctx.shared_memory.get("vars", {})
    user_uttr = state_utils.get_last_human_utterance(vars)
    flag = is_yes(user_uttr)
    return flag


def always_true(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    return True


def facts(ctx: Context, actor: Actor, *args, **kwargs):
    return provide_facts_request(ctx, actor, *args, **kwargs)

def no_intent(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    vars = ctx.shared_memory.get("vars", {})
    user_uttr = state_utils.get_last_human_utterance(vars)
    flag = is_no(user_uttr)
    return flag


def donot_know_intent(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    vars = ctx.shared_memory.get("vars", {})
    user_uttr = state_utils.get_last_human_utterance(vars)
    flag = is_donot_know(user_uttr)
    return flag
