import logging
import common.utils as common_utils
import common.dff.integration.context as int_ctx
import scenario.response_funcs as response_funcs

from df_engine.core import Actor, Context

from common.constants import MUST_CONTINUE
from common.dff.integration.context import (
    get_last_human_utterance,
    get_shared_memory,
    save_to_shared_memory,
    set_can_continue,
    set_confidence,
)

logger = logging.getLogger(__name__)

def intent_catcher_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:

    intents_by_catcher = common_utils.get_intents(
        int_ctx.get_last_human_utterance(ctx, actor), probs=False, which="intent_catcher"
    )
    
    response = ""
    if (len(intents_by_catcher) > 0):
        intention = intents_by_catcher[0]
        logger.debug(f"Intent is defined as {intention}")
        funcs = response_funcs.get_respond_funcs()[intention]
        response = funcs(ctx, actor, intention)
    else:
        logger.debug("Intent is not defined")
        response = default_response(ctx, actor)

    return response

def default_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    logger.debug("default response")
    return response_funcs.random_respond(ctx, actor, "dont_understand")