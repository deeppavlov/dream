import logging, re
from . import response as loc_rsp

from dff.core import Context, Actor

logger = logging.getLogger(__name__)


def has_story_type(ctx: Context, actor: Actor) -> bool:
    return bool(loc_rsp.get_story_type(ctx, actor))


def has_story_left(ctx: Context, actor: Actor) -> bool:
    return bool(loc_rsp.get_story_left(ctx, actor))


def is_tell_me_a_story(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    return str(ctx.misc.get("intents", {}).get("tell_me_a_story", {}).get("detected", "")) == "1"


def is_asked_for_a_story(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    prev_node = loc_rsp.get_previous_node(ctx)
    return prev_node != "which_story_node"
