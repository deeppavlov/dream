import logging
import re

from dff.core import Context, Actor

# from common.utils import is_yes, is_no, is_donot_know


logger = logging.getLogger(__name__)
# ....


def yes_intent(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    # vars = ctx.shared_memory.get("vars", {})
    # user_uttr = state_utils.get_last_human_utterance(vars)
    # flag = is_yes(user_uttr)
    flag = bool(re.compile(r"\byes\b").search(ctx.last_request))
    return flag


def always_true(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    return True


def no_intent(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    # vars = ctx.shared_memory.get("vars", {})
    # user_uttr = state_utils.get_last_human_utterance(vars)
    # flag = is_no(user_uttr)
    flag = bool(re.compile(r"\bno\b").search(ctx.last_request))
    return flag


def donot_know_intent(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    # vars = ctx.shared_memory.get("vars", {})
    # user_uttr = state_utils.get_last_human_utterance(vars)
    # flag = is_donot_know(user_uttr)
    flag = bool(re.compile(r"\bnot know").search(ctx.last_request))
    return flag
