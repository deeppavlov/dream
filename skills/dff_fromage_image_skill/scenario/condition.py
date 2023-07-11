import logging
from df_engine.core import Context, Actor

logger = logging.getLogger(__name__)
logger.setLevel(logging.NOTSET)


def caption_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    return True
