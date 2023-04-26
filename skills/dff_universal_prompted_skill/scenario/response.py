import json
import logging
import re
import requests
import sentry_sdk
from os import getenv
from typing import Any

import common.dff.integration.context as int_ctx
import common.dff.integration.response as int_rsp
from common.constants import CAN_NOT_CONTINUE
from df_engine.core import Context, Actor


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
GENERATIVE_TIMEOUT = int(getenv("GENERATIVE_TIMEOUT", 5))
N_UTTERANCES_CONTEXT = int(getenv("N_UTTERANCES_CONTEXT", 3))

FIX_PUNCTUATION = re.compile(r"\s(?=[\.,:;])")
DEFAULT_CONFIDENCE = 0.9
LOW_CONFIDENCE = 0.7
DEFAULT_PROMPT = "Respond like a friendly chatbot."

CONSIDERED_LM_SERVICES = {
    "GPT-J 6B": {
        "url": "http://transformers-lm-gptj:8130/respond",
        "config": json.load(open("generative_configs/default_generative_config.json", "r")),
    },
    "BLOOMZ 7B": {
        "url": "http://transformers-lm-bloomz7b:8146/respond",
        "config": json.load(open("generative_configs/default_generative_config.json", "r")),
    },
    "ChatGPT": {
        "url": "http://openai-api-chatgpt:8145/respond",
        "config": json.load(open("generative_configs/openai-chatgpt.json", "r")),
        "envvars_to_send": ["OPENAI_API_KEY", "OPENAI_ORGANIZATION"],
    },
    "GPT-3.5": {
        "url": "http://openai-api-davinci3:8131/respond",
        "config": json.load(open("generative_configs/openai-text-davinci-003.json", "r")),
        "envvars_to_send": ["OPENAI_API_KEY", "OPENAI_ORGANIZATION"],
    },
    "Open-Assistant SFT-1 12B": {
        "url": "http://transformers-lm-oasst12b:8158/respond",
        "config": json.load(open("generative_configs/default_generative_config.json", "r")),
    },
}


def compose_data_for_model(ctx, actor):
    # consider N_UTTERANCES_CONTEXT last utterances
    context = int_ctx.get_utterances(ctx, actor)[-N_UTTERANCES_CONTEXT:]
    context = [uttr.get("text", "") for uttr in context]

    if context:
        context = [re.sub(FIX_PUNCTUATION, "", x) for x in context]

    # drop the dialog history when prompt changes
    last_uttr = int_ctx.get_last_human_utterance(ctx, actor)
    # get prompt from the current utterance attributes
    given_prompt = last_uttr.get("attributes", {}).get("prompt", DEFAULT_PROMPT)
    history = int_ctx.get_utterances(ctx, actor)

    for i in range(1, len(history) + 1, 2):
        curr_prompt = history[-i].get("attributes", {}).get("prompt", DEFAULT_PROMPT)
        # checking only user utterances
        if curr_prompt != given_prompt:
            # cut context on the last user utterance utilizing the current prompt
            context = context[-i + 2 :]
            break

    return context


def if_none_var_values(sending_variables):
    if len(sending_variables.keys()) > 0 and all([var_value[0] is None for var_value in sending_variables.values()]):
        return True
    else:
        False


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
    logger.info(f"dialog_context: {dialog_context}")
    last_uttr = int_ctx.get_last_human_utterance(ctx, actor)
    prompt = last_uttr.get("attributes", {}).get("prompt", DEFAULT_PROMPT)
    logger.info(f"prompt: {prompt}")
    lm_service = last_uttr.get("attributes", {}).get("lm_service", "GPT-J 6B")
    logger.info(f"lm_service: {lm_service}")

    if "envvars_to_send" in CONSIDERED_LM_SERVICES[lm_service]:
        # get variables which names are in `ENVVARS_TO_SEND` (splitted by comma if many)
        # from user_utterance attributes or from environment
        envvars_to_send = CONSIDERED_LM_SERVICES[lm_service]["envvars_to_send"]
        human_uttr_attributes = int_ctx.get_last_human_utterance(ctx, actor).get("attributes", {})
        sending_variables = {f"{var}_list": [human_uttr_attributes.get(var.lower(), None)] for var in envvars_to_send}
        if if_none_var_values(sending_variables):
            sending_variables = {f"{var}_list": [getenv(var, None)] for var in envvars_to_send}
            if if_none_var_values(sending_variables):
                logger.info(f"Did not get {envvars_to_send}'s values. Sending without them.")
            else:
                logger.info(f"Got {envvars_to_send}'s values from environment.")
        else:
            logger.info(f"Got {envvars_to_send}'s values from attributes.")
    else:
        sending_variables = {}

    if len(dialog_context) > 0:
        try:
            response = requests.post(
                CONSIDERED_LM_SERVICES[lm_service]["url"],
                json={
                    "dialog_contexts": [dialog_context],
                    "prompts": [prompt],
                    "configs": [CONSIDERED_LM_SERVICES[lm_service]["config"]],
                    **sending_variables,
                },
                timeout=GENERATIVE_TIMEOUT,
            )
            hypotheses = response.json()[0]
        except Exception as e:
            sentry_sdk.capture_exception(e)
            logger.exception(e)
            hypotheses = []
    else:
        hypotheses = []
    logger.info(f"generated hypotheses: {hypotheses}")
    for hyp in hypotheses:
        confidence = DEFAULT_CONFIDENCE
        hyp_text = " ".join(hyp.split())
        if len(hyp_text) and hyp_text[-1] not in [".", "?", "!"]:
            hyp_text += "."
            confidence = LOW_CONFIDENCE
        gathering_responses(hyp_text, confidence, {}, {}, {"can_continue": CAN_NOT_CONTINUE})

    if len(curr_responses) == 0:
        return ""

    return int_rsp.multi_response(
        replies=curr_responses,
        confidences=curr_confidences,
        human_attr=curr_human_attrs,
        bot_attr=curr_bot_attrs,
        hype_attr=curr_attrs,
    )(ctx, actor, *args, **kwargs)
