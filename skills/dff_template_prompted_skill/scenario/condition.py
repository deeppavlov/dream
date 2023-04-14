import logging

from df_engine.core import Actor, Context
import common.dff.integration.context as int_ctx


logger = logging.getLogger(__name__)


def if_updating_prompt(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    human_uttr = int_ctx.get_human_utterances(ctx, actor).get("text", "")
    if "/prompt" in human_uttr:
        return True
    return False
