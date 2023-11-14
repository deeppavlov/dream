import json
import logging
import re
import sentry_sdk
from os import getenv
from typing import Any

import common.dff.integration.context as int_ctx
import common.dff.integration.response as int_rsp
from common.constants import CAN_NOT_CONTINUE
from common.prompts import send_request_to_prompted_generative_service, compose_sending_variables
from df_engine.core import Context, Actor


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
GENERATIVE_TIMEOUT = float(getenv("GENERATIVE_TIMEOUT", 5))
GENERATIVE_SERVICE_URL = getenv("GENERATIVE_SERVICE_URL")
GENERATIVE_SERVICE_CONFIG = getenv("GENERATIVE_SERVICE_CONFIG")
USE_KG_DATA = int(getenv("USE_KG_DATA", 0))
USER_KG_SERVICE_URL = getenv("USER_KG_SERVICE_URL")
if GENERATIVE_SERVICE_CONFIG:
    with open(f"common/generative_configs/{GENERATIVE_SERVICE_CONFIG}", "r") as f:
        GENERATIVE_SERVICE_CONFIG = json.load(f)

PROMPT_FILE = getenv("PROMPT_FILE")
N_UTTERANCES_CONTEXT = int(getenv("N_UTTERANCES_CONTEXT", 3))
ENVVARS_TO_SEND = getenv("ENVVARS_TO_SEND", None)
ENVVARS_TO_SEND = [] if ENVVARS_TO_SEND is None else ENVVARS_TO_SEND.split(",")

assert GENERATIVE_SERVICE_URL
assert PROMPT_FILE
assert USER_KG_SERVICE_URL

with open(PROMPT_FILE, "r") as f:
    PROMPT_DICT = json.load(f)
PROMPT = PROMPT_DICT["prompt"]

FIX_PUNCTUATION = re.compile(r"\s(?=[\.,:;])")
PROMPT_REPLACEMENT_COMMAND = re.compile(r"^/prompt")
PROMPT_RESET_COMMAND = re.compile(r"^/resetprompt")
DEFAULT_CONFIDENCE = 0.9
SUPER_CONFIDENCE = 1.0
LOW_CONFIDENCE = 0.7


def compose_data_for_model(ctx, actor):
    # consider N_UTTERANCES_CONTEXT last utterances
    context = int_ctx.get_utterances(ctx, actor)[-N_UTTERANCES_CONTEXT:]
    context = [uttr.get("text", "") for uttr in context]

    if context:
        context = [re.sub(FIX_PUNCTUATION, "", x) for x in context]

    return context


def generative_response(ctx: Context, actor: Actor, *args, **kwargs) -> Any:
    curr_responses, curr_confidences, curr_human_attrs, curr_bot_attrs, curr_attrs = (
        [],
        [],
        [],
        [],
        [],
    )

    def gathering_responses(reply, confidence, human_attr, bot_attr, attr):
        nonlocal curr_responses, curr_confidences, curr_human_attrs, curr_bot_attrs, curr_attrs
        if reply and confidence:
            curr_responses += [reply]
            curr_confidences += [confidence]
            curr_human_attrs += [human_attr]
            curr_bot_attrs += [bot_attr]
            curr_attrs += [attr]

    dialog_context = compose_data_for_model(ctx, actor)
    # get variables which names are in `ENVVARS_TO_SEND` (splitted by comma if many)
    # from user_utterance attributes or from environment
    human_uttr_attributes = int_ctx.get_last_human_utterance(ctx, actor).get("attributes", {})
    lm_service_kwargs = human_uttr_attributes.pop("lm_service_kwargs", None)
    lm_service_kwargs = {} if lm_service_kwargs is None else lm_service_kwargs
    envvars_to_send = ENVVARS_TO_SEND if len(ENVVARS_TO_SEND) else human_uttr_attributes.get("envvars_to_send", [])
    sending_variables = compose_sending_variables(
        lm_service_kwargs,
        envvars_to_send,
        **human_uttr_attributes,
    )

    shared_memory = int_ctx.get_shared_memory(ctx, actor)
    prompt = shared_memory.get("prompt", "")
    prompt = PROMPT

    custom_el = (
        ctx.misc.get("agent", {})
        .get("dialog", {})
        .get("human_utterances", [{}])[-1]
        .get("annotations", {})
        .get("custom_entity_linking")
    )
    user_kg = (
        ctx.misc.get("agent", {})
        .get("dialog", {})
        .get("human_utterances", [{}])[-1]
        .get("annotations", {})
        .get("user_knowledge_memorizer")
    )
    logger.info(f"custom_el: {custom_el}")
    logger.info(f"user_kg: {user_kg}")

    if USE_KG_DATA and user_kg and (kg_prompt := user_kg["kg_prompt"]):
        kg_prompt = re.sub(r"[-\n]", "", kg_prompt[0].lower()).split(".")
        kg_prompt = ",".join(kg_prompt)
        prompt = prompt + f"\n\nADDITIONAL INSTRUCTION: You know that {kg_prompt}. Use these facts in your answer."

    logger.info(f"prompt: {prompt}")
    logger.info(f"dialog_context: {dialog_context}")

    if len(dialog_context) > 0:
        try:
            hypotheses = send_request_to_prompted_generative_service(
                dialog_context,
                prompt,
                GENERATIVE_SERVICE_URL,
                GENERATIVE_SERVICE_CONFIG,
                GENERATIVE_TIMEOUT,
                sending_variables,
            )
        except Exception as e:
            sentry_sdk.capture_exception(e)
            logger.exception(e)
            hypotheses = []
    else:
        hypotheses = []
    logger.info(f"generated hypotheses: {hypotheses}")

    for hyp in hypotheses:
        confidence = DEFAULT_CONFIDENCE
        if len(hyp) and hyp[-1] not in [".", "?", "!"]:
            hyp += "."
            confidence = LOW_CONFIDENCE
        _curr_attrs = {"can_continue": CAN_NOT_CONTINUE}
        gathering_responses(hyp, confidence, {}, {}, _curr_attrs)

    if len(curr_responses) == 0:
        return ""

    return int_rsp.multi_response(
        replies=curr_responses,
        confidences=curr_confidences,
        human_attr=curr_human_attrs,
        bot_attr=curr_bot_attrs,
        hype_attr=curr_attrs,
    )(ctx, actor, *args, **kwargs)


def updating_prompt_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    human_uttr = int_ctx.get_last_human_utterance(ctx, actor).get("text", "")
    prompt = PROMPT_REPLACEMENT_COMMAND.sub("", human_uttr).strip()
    int_ctx.save_to_shared_memory(ctx, actor, prompt=prompt)

    int_ctx.set_confidence(ctx, actor, SUPER_CONFIDENCE)
    return (
        "Saved the new prompt for you. "
        "To update the prompt, type in `/prompt prompttext` again. "
        "To reset the prompt to the default one, use `/resetprompt` command."
    )


def reseting_prompt_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    int_ctx.save_to_shared_memory(ctx, actor, prompt=PROMPT)
    int_ctx.set_confidence(ctx, actor, SUPER_CONFIDENCE)
    return f"Reset the prompt to the default one for you:\n{PROMPT}"
