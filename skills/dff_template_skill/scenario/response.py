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
    intention, confidence = get_detected_intents(int_ctx.get_last_human_utterance(ctx, actor))

    response = ""
    if intention is not None and confidence > 0:
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


def set_confidence_from_input(ctx: Context, actor: Actor, *args, **kwargs) -> Context:
    _, confidence = get_detected_intents(int_ctx.get_last_human_utterance(ctx, actor))
    int_ctx.set_confidence(ctx, actor, confidence)
    return ctx


def get_detected_intents(annotated_utterance):
    annotations = annotated_utterance.get("annotations", {})
    intents = annotations.get("intent_catcher", {})
    intent, confidence = None, 0
    for key, value in intents.items():
        if value.get("detected", 0) == 1:
            confidence_current = value.get("confidence", 0.0)
            if confidence_current > confidence:
                intent, confidence = key, confidence_current

    return intent, confidence
