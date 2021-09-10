import logging

from dff.core import Context, Actor

logger = logging.getLogger(__name__)

def get_previous_node(ctx:Context) -> str:
    try:
        return [node_tuple[1] for node_tuple in ctx.node_labels.values()][-2]
    except:
        return "start_node"

def is_tell_me_a_story(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    print(ctx.misc.get("intents",""))
    return ctx.misc.get("intents","") == "tell_me_a_story"

def is_asked_for_a_story(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    prev_node = get_previous_node(ctx)
    return prev_node != "which_story_node"