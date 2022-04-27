import re
import logging

from df_engine.core import Context, Actor

from common.dff.integration import condition as int_cnd

logger = logging.getLogger(__name__)
# ....


def example_lets_talk_about():
    def example_lets_talk_about_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        return int_cnd.is_lets_chat_about_topic_human_initiative(ctx, actor)

    return example_lets_talk_about_handler


def is_detailed():
    def has_cond(ctx: Context, actor: Actor, *args, **kwargs):
        return bool(len(ctx.last_request) > 30)

    return has_cond


