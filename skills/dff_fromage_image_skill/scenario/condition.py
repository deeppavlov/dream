import logging

from df_engine.core import Context, Actor
import common.dff.integration.context as int_ctx

logger = logging.getLogger(__name__)
logger.setLevel(logging.NOTSET)


def caption_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    caption = int_ctx.get_last_human_utterance(ctx, actor).get("annotations", {}).get("fromage", {})
    if caption != "" and caption is not None:
        return True
    return False
