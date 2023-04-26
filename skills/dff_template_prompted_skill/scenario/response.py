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
GENERATIVE_SERVICE_URL = getenv("GENERATIVE_SERVICE_URL")
GENERATIVE_SERVICE_CONFIG = getenv("GENERATIVE_SERVICE_CONFIG")
if GENERATIVE_SERVICE_CONFIG:
    with open(f"generative_configs/{GENERATIVE_SERVICE_CONFIG}", "r") as f:
        GENERATIVE_SERVICE_CONFIG = json.load(f)

PROMPT_FILE = getenv("PROMPT_FILE")
N_UTTERANCES_CONTEXT = int(getenv("N_UTTERANCES_CONTEXT", 3))
ALLOW_PROMPT_RESET = int(getenv("ALLOW_PROMPT_RESET", 0))
ENVVARS_TO_SEND = getenv("ENVVARS_TO_SEND", None)
ENVVARS_TO_SEND = [] if ENVVARS_TO_SEND is None else ENVVARS_TO_SEND.split(",")
sending_variables = {f"{var}_list": [getenv(var, None)] for var in ENVVARS_TO_SEND}
# check if at least one of the env variables is not None
if len(sending_variables.keys()) > 0 and all([var_value is None for var_value in sending_variables.values()]):
    raise NotImplementedError(
        "ERROR: All environmental variables have None values. At least one of the variables must have not None value"
    )

assert GENERATIVE_SERVICE_URL
assert PROMPT_FILE

with open(PROMPT_FILE, "r") as f:
    PROMPT = json.load(f)["prompt"]

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

    history = int_ctx.get_utterances(ctx, actor)
    for i in range(1, len(history) + 1, 2):
        is_new_prompt = re.search(PROMPT_REPLACEMENT_COMMAND, history[-i].get("text", ""))
        is_reset_prompt = re.search(PROMPT_RESET_COMMAND, history[-i].get("text", ""))
        if ALLOW_PROMPT_RESET and (is_new_prompt or is_reset_prompt):
            # cut context on the last user utterance utilizing the current prompt
            context = context[-i + 2 :]
            break

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

    shared_memory = int_ctx.get_shared_memory(ctx, actor)
    prompt = shared_memory.get("prompt", "")

    logger.info(f"dialog_context: {dialog_context}")
    if len(dialog_context) > 0:
        try:
            response = requests.post(
                GENERATIVE_SERVICE_URL,
                json={
                    "dialog_contexts": [dialog_context],
                    "prompts": [prompt if len(prompt) > 0 and ALLOW_PROMPT_RESET else PROMPT],
                    "configs": [GENERATIVE_SERVICE_CONFIG],
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
        hyp = hyp.replace(" ".join(PROMPT.split()), "")
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
