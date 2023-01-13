from ast import Import
import json
import random
import logging
import common.dff.integration.context as int_ctx
import common.utils
import scenario.response_funcs as response_funcs
from df_engine.core import Context, Actor

INTENT_RESPONSES_PATH = "scenario/data/intent_response_phrases.json"

logger = logging.getLogger(__name__)
# ....
with open(INTENT_RESPONSES_PATH, "r") as fp:
    RESPONSES = json.load(fp)

def response_for_intent(intent: str):
    response = ""
    if intent is not None:
        logger.debug(f"Intent is defined as {intent}")

        response_phrases = RESPONSES[intent]
        response = random.choice(response_phrases).strip()

        # funcs = response_funcs.get_response_funcs()[intent]
        # response = funcs(ctx, actor, intent)
    else:
        logger.debug("Intent is not defined")

    if response == "":
        logger.error(f"response is empty for intents")

    return response


def default_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    annotated_utterance = int_ctx.get_last_human_utterance(ctx, actor)
    logger.error(f"response is empty for intents")
    return ""


# re-using the code from common
def get_intents(annotated_utterance):
    return common.utils.get_intents(annotated_utterance, probs=False, which="minecraft_bot")
    # annotations = annotated_utterance.get("annotations", {})
    # return annotations.get("intent_catcher", {})


def get_detected_intents(annotated_utterance):
    intents = get_intents(annotated_utterance)
    intent, confidence = None, 0.0

    logger.info(f"intents: {intents}")

    # for key, value in intents.items():
    #     if value.get("detected", 0) == 1:
    #         confidence_current = value.get("confidence", 0.0)
    #         if confidence_current > confidence:
    #             intent, confidence = key, confidence_current

    return intent, confidence


def set_confidence_from_input(ctx: Context, actor: Actor, *args, **kwargs) -> Context:
    _, confidence = get_detected_intents(int_ctx.get_last_human_utterance(ctx, actor))
    int_ctx.set_confidence(ctx, actor, confidence)
    return ctx


def name_given_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    for slot_name, slot_value in ctx.misc.get("slots", {}).items():
        if slot_name == "minecraft_new_known_object":
            return f"Gotcha! Now if ask me to build {slot_value} -- I can do it seamlessly without any instructions!"

    return "Gotcha! Now if ask me to build it -- I can do it seamlessly without any instructions!"