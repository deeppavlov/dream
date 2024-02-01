import logging
import requests
import os
from copy import deepcopy

import common.dff.integration.context as int_ctx
import scenario.response_funcs as response_funcs
from common.robot import command_intents
from common.utils import get_intents
from df_engine.core import Actor, Context


logger = logging.getLogger(__name__)

ROS_FLASK_SERVER = os.getenv("ROS_FLASK_SERVER")


def command_selector_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    annotated_utterance = int_ctx.get_last_human_utterance(ctx, actor)
    intention, confidence = get_detected_intents(annotated_utterance)
    logger.info(f"Detected intents: {intention}")

    response, conf, human_attr, bot_attr, attr = "", 0.0, {}, {}, {}
    if intention is not None and confidence > 0 and intention in response_funcs.get_respond_funcs():
        logger.debug(f"Intent is defined as {intention}")
        dialog = int_ctx.get_dialog(ctx, actor)
        dialog["seen"] = dialog["called_intents"][intention]
        funcs = response_funcs.get_respond_funcs()[intention]
        response = funcs(ctx, actor)
        if not isinstance(response, str):
            conf = deepcopy(response[1])
            human_attr = deepcopy(response[2])
            bot_attr = deepcopy(response[3])
            attr = deepcopy(response[4])
            response = deepcopy(response[0])
        # Special formatter which used in AWS Lambda to identify what was the intent
        while "#+#" in response:
            response = response[: response.rfind(" #+#")]
        logger.info(f"Response: {response}; intent_name: {intention}")
        try:
            response += " #+#{}".format(intention)
            logger.debug(f"senging {intention} to {ROS_FLASK_SERVER}/perform_command...")
            requests.post(ROS_FLASK_SERVER + '/perform_command', json={'command': intention})
        except TypeError:
            logger.error(f"TypeError intent_name: {intention} response: {response};")
            response = "Hmmm... #+#{}".format(intention)
        # todo: we need to know what intent was called
        # current workaround is to use only one intent if several were detected
        # and to append special token with intent_name
    else:
        logger.debug("Intent is not defined")

    if response == "":
        intents = get_intents(annotated_utterance, probs=True, which="intent_catcher")
        logger.error(f"response is empty for intents: {intents}")
    elif conf == 0.0:
        return response
    return [[response, conf, human_attr, bot_attr, attr]]


def default_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    annotated_utterance = int_ctx.get_last_human_utterance(ctx, actor)

    intents = get_intents(annotated_utterance, probs=True, which="intent_catcher")
    logger.error(f"response is empty for intents: {intents}")
    return ""


def set_confidence_from_input(ctx: Context, actor: Actor, *args, **kwargs) -> Context:
    intent, confidence = get_detected_intents(int_ctx.get_last_human_utterance(ctx, actor))
    if intent in command_intents:
        int_ctx.set_confidence(ctx, actor, 1.0)
    else:
        int_ctx.set_confidence(ctx, actor, confidence)
    return ctx


def get_detected_intents(annotated_utterance):
    intents = get_intents(annotated_utterance, probs=True, which="intent_catcher")
    intent, confidence = None, 0.0
    for intent_name, intent_conf in intents.items():
        if intent_conf > 0 and intent_name in response_funcs.get_respond_funcs():
            confidence_current = intent_conf
            if confidence_current > confidence:
                intent, confidence = intent_name, float(confidence_current)

    return intent, confidence

