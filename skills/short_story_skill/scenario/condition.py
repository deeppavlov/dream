import logging

from dff.core import Context, Actor

from common.dff.integration import condition as int_cnd

logger = logging.getLogger(__name__)
# ....


def is_tell_me_a_story(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    print(ctx.misc.get("intents",""))
    return ctx.misc.get("intents","") == "tell_me_a_story"

def is_asked_for_a_story(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    try:
        prev_node = [node_tuple[1] for node_tuple in ctx.node_labels.values()][-2]
    except:
        prev_node = None
    return prev_node != "which_story_node"
