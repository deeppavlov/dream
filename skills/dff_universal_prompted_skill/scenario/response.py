import json
import logging
import re
import requests
import sentry_sdk
from copy import deepcopy
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
DEFAULT_LM_SERVICE_URL = getenv("DEFAULT_LM_SERVICE_URL", "http://transformers-lm-oasst12b:8158/respond")
DEFAULT_LM_SERVICE_CONFIG = getenv("DEFAULT_LM_SERVICE_CONFIG", "default_generative_config.json")
DEFAULT_LM_SERVICE_CONFIG = json.load(open(f"generative_configs/{DEFAULT_LM_SERVICE_CONFIG}", "r"))
ENVVARS_TO_SEND = {
    "http://transformers-lm-gptj:8130/respond": [],
    "http://transformers-lm-bloomz7b:8146/respond": [],
    "http://transformers-lm-oasst12b:8158/respond": [],
    "http://openai-api-chatgpt:8145/respond": ["OPENAI_API_KEY", "OPENAI_ORGANIZATION"],
    "http://openai-api-davinci3:8131/respond": ["OPENAI_API_KEY", "OPENAI_ORGANIZATION"],
    "http://openai-api-gpt4:8159/respond": ["OPENAI_API_KEY", "OPENAI_ORGANIZATION"],
    "http://openai-api-gpt4-32k:8160/respond": ["OPENAI_API_KEY", "OPENAI_ORGANIZATION"],
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
    if len(sending_variables.keys()) > 0 and all(
        [var_value[0] is None or var_value[0] == "" for var_value in sending_variables.values()]
    ):
        return True
    return False


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
    human_uttr_attributes = int_ctx.get_last_human_utterance(ctx, actor).get("attributes", {})
    prompt = human_uttr_attributes.get("prompt", DEFAULT_PROMPT)
    logger.info(f"prompt: {prompt}")
    lm_service_url = human_uttr_attributes.get("lm_service_url", DEFAULT_LM_SERVICE_URL)
    logger.info(f"lm_service_url: {lm_service_url}")
    # this is a dictionary! not a file!
    lm_service_config = human_uttr_attributes.get("lm_service_config", None)
    lm_service_kwargs = human_uttr_attributes.get("lm_service_kwargs", None)
    lm_service_kwargs = {} if lm_service_kwargs is None else lm_service_kwargs
    envvars_to_send = ENVVARS_TO_SEND.get(lm_service_url, [])

    if len(envvars_to_send):
        # get variables which names are in `envvars_to_send` (splitted by comma if many)
        # from the last human utterance's attributes
        sending_variables = {
            f"{var.lower()}s": [human_uttr_attributes.get(var.lower(), None)] for var in envvars_to_send
        }
        if if_none_var_values(sending_variables):
            # get variables which names are in `envvars_to_send` (splitted by comma if many)
            # from env variables
            sending_variables = {f"{var.lower()}s": [getenv(var, None)] for var in envvars_to_send}
            if if_none_var_values(sending_variables):
                logger.info(f"Did not get {envvars_to_send}'s values. Sending without them.")
            else:
                logger.info(f"Got {envvars_to_send}'s values from environment.")
        else:
            logger.info(f"Got {envvars_to_send}'s values from attributes.")
    else:
        sending_variables = {}

    # adding kwargs to request from the last human utterance's attributes
    for _key, _value in lm_service_kwargs.items():
        logger.info(f"Got/Re-writing {_key}s values from kwargs.")
        sending_variables[f"{_key}s"] = [deepcopy(_value)]

    if len(dialog_context) > 0:
        try:
            response = requests.post(
                lm_service_url,
                json={
                    "dialog_contexts": [dialog_context],
                    "prompts": [prompt],
                    "configs": [lm_service_config],
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
