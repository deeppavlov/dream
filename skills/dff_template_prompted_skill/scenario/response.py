import json
import logging
import re
import sentry_sdk
import time
from os import getenv
from pathlib import Path
from typing import Any

import common.dff.integration.context as int_ctx
import common.dff.integration.response as int_rsp
from common.constants import CAN_NOT_CONTINUE
from common.containers import get_envvars_for_llm, is_container_running
from common.prompts import send_request_to_prompted_generative_service, get_goals_from_prompt, compose_sending_variables
from df_engine.core import Context, Actor


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
GENERATIVE_SERVICE_URL = getenv("GENERATIVE_SERVICE_URL")

while True:
    result = is_container_running(GENERATIVE_SERVICE_URL)
    if result:
        logger.info(f"GENERATIVE_SERVICE_URL: {GENERATIVE_SERVICE_URL} is ready")
        break
    else:
        time.sleep(5)
        continue

GENERATIVE_SERVICE_CONFIG = getenv("GENERATIVE_SERVICE_CONFIG")
if GENERATIVE_SERVICE_CONFIG:
    with open(f"common/generative_configs/{GENERATIVE_SERVICE_CONFIG}", "r") as f:
        GENERATIVE_SERVICE_CONFIG = json.load(f)

GENERATIVE_TIMEOUT = float(getenv("GENERATIVE_TIMEOUT", 5))
GENERATIVE_TIMEOUT = (
    GENERATIVE_SERVICE_CONFIG.pop("timeout", GENERATIVE_TIMEOUT) if GENERATIVE_SERVICE_CONFIG else GENERATIVE_TIMEOUT
)

PROMPT_FILE = getenv("PROMPT_FILE")
N_UTTERANCES_CONTEXT = int(getenv("N_UTTERANCES_CONTEXT", 3))
N_UTTERANCES_CONTEXT = (
    GENERATIVE_SERVICE_CONFIG.pop("n_utterances_context", N_UTTERANCES_CONTEXT)
    if GENERATIVE_SERVICE_CONFIG
    else N_UTTERANCES_CONTEXT
)

ALLOW_PROMPT_RESET = int(getenv("ALLOW_PROMPT_RESET", 0))
ENVVARS_TO_SEND = get_envvars_for_llm(GENERATIVE_SERVICE_URL)

assert GENERATIVE_SERVICE_URL
assert PROMPT_FILE

with open(PROMPT_FILE, "r") as f:
    PROMPT_DICT = json.load(f)
PROMPT = PROMPT_DICT["prompt"]
GOALS_FROM_PROMPT = PROMPT_DICT.get("goals", "")

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
    # get variables which names are in `ENVVARS_TO_SEND` (splitted by comma if many)
    # from user_utterance attributes or from environment
    human_uttr_attributes = int_ctx.get_last_human_utterance(ctx, actor).get("attributes", {})
    lm_service_kwargs = human_uttr_attributes.get("lm_service", {}).get("kwargs", None)
    lm_service_kwargs = {} if lm_service_kwargs is None else lm_service_kwargs
    sending_variables = compose_sending_variables(
        lm_service_kwargs,
        ENVVARS_TO_SEND,
        human_uttr_attributes,
    )

    shared_memory = int_ctx.get_shared_memory(ctx, actor)
    prompt = shared_memory.get("prompt", "")
    prompt = prompt if len(prompt) > 0 and ALLOW_PROMPT_RESET else PROMPT
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

    # if we do not have a goals from prompt, extract them using generative model (at most once in a dialog)
    goals_from_prompt = ""
    prompt_name = Path(PROMPT_FILE).stem
    if not GOALS_FROM_PROMPT:
        # get already collected goals from prompts from human attributes
        prev_prompts_goals = int_ctx.get_prompts_goals(ctx, actor)
        goals_from_prompt = prev_prompts_goals.get(prompt_name, "")
        if not goals_from_prompt:
            # if current prompt's goals are empty in human attributes, generate them!
            goals_from_prompt = get_goals_from_prompt(
                prompt=PROMPT,
                url=GENERATIVE_SERVICE_URL,
                generative_timeout=GENERATIVE_TIMEOUT,
                sending_variables=sending_variables,
            )
            logger.info(f"Generated goals for prompt using generative service:\n{goals_from_prompt}")
        else:
            logger.info("Found goals for prompt from the human attributes")

    for hyp in hypotheses:
        confidence = DEFAULT_CONFIDENCE
        if len(hyp) and hyp[-1] not in [".", "?", "!"]:
            hyp += "."
            confidence = LOW_CONFIDENCE
        _curr_attrs = {
            "can_continue": CAN_NOT_CONTINUE,
        }
        if goals_from_prompt:
            _curr_attrs["prompts_goals"] = {prompt_name: goals_from_prompt}
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
