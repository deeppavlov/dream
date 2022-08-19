import logging

from df_engine.core import Context, Actor

from common.dff.integration import condition as int_cnd

logger = logging.getLogger(__name__)
# ....


def prev_is_question(ctx: Context, actor: Actor) -> bool:
    return True


def has_story_intent(ctx: Context, actor: Actor) -> bool:
    return True

