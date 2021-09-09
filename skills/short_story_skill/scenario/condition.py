import logging

from dff.core import Context, Actor

from common.dff.integration import condition as int_cnd

logger = logging.getLogger(__name__)
# ....


def is_tell_me_a_story(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    print(ctx.misc.get("intents",""))
    return ctx.misc.get("intents","") == "tell_me_a_story"


def is_tell_me_a_story(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    print(ctx.misc.get("intents",""))
    return ctx.misc.get("intents","") == "tell_me_a_story"


def is_tell_me_a_story(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    print(ctx.misc.get("intents",""))
    return ctx.misc.get("intents","") == "tell_me_a_story"


# def example_lets_talk_about():
#     def example_lets_talk_about_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
#         return int_cnd.is_lets_chat_about_topic_human_initiative(ctx, actor)

#     return example_lets_talk_about_handler
