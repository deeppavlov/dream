import asyncio
import json
import logging
import re
from os import getenv
from typing import Any

import aiohttp
import sentry_sdk

import common.dff.integration.context as int_ctx
import common.dff.integration.response as int_rsp
from common.constants import CAN_NOT_CONTINUE
from common.containers import get_envvars_for_llm
from common.prompts import compose_sending_variables
from df_engine.core import Context, Actor


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
DEFAULT_LM_SERVICE_TIMEOUT = float(getenv("DEFAULT_LM_SERVICE_TIMEOUT", 5))
N_UTTERANCES_CONTEXT = int(getenv("N_UTTERANCES_CONTEXT", 3))

FIX_PUNCTUATION = re.compile(r"\s(?=[\.,:;])")
DEFAULT_CONFIDENCE = 0.9
LOW_CONFIDENCE = 0.7
DEFAULT_PROMPT = "Respond like a friendly chatbot."
DEFAULT_LM_SERVICE_URL = getenv("DEFAULT_LM_SERVICE_URL", "http://transformers-lm-gptjt:8161/respond")
DEFAULT_LM_SERVICE_CONFIG = getenv("DEFAULT_LM_SERVICE_CONFIG", "default_generative_config.json")
DEFAULT_LM_SERVICE_CONFIG = json.load(open(f"common/generative_configs/{DEFAULT_LM_SERVICE_CONFIG}", "r"))


def compose_data_for_model(ctx, actor):
    context = [uttr.get("text", "") for uttr in int_ctx.get_utterances(ctx, actor)]

    if context:
        context = [re.sub(FIX_PUNCTUATION, "", x) for x in context]

    # drop the dialog history when prompt changes
    last_uttr = int_ctx.get_last_human_utterance(ctx, actor)
    # get prompt from the current utterance attributes
    given_skills = last_uttr.get("attributes", {}).get("skills", [])
    history = int_ctx.get_utterances(ctx, actor)

    for i in range(1, len(history) + 1, 2):
        # checking only user utterances
        if history[-i].get("attributes", {}).get("skills", []) != given_skills:
            # cut context on the last user utterance utilizing the current prompt
            context = context[-i + 2 :]
            break

    return context


async def async_request_to_prompted_generative_service(
    session, dialog_context, prompt, url, config, timeout, lm_service_kwargs, skill_name, human_uttr_attributes
):
    logger.info(f"lm_service_url: {url}")
    logger.info(f"prompt: {prompt}")
    envvars_to_send = get_envvars_for_llm(url)
    sending_variables = compose_sending_variables(
        lm_service_kwargs,
        envvars_to_send,
        human_uttr_attributes,
    )
    try:
        async with session.post(
            url,
            json={
                "dialog_contexts": [dialog_context],
                "prompts": [prompt],
                "configs": [config],
                **sending_variables,
            },
            timeout=aiohttp.ClientTimeout(timeout),
        ) as resp:
            hypotheses = (await resp.json())[0]
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
        hypotheses = []
    logger.info(f"generated hypotheses: {hypotheses}")

    curr_responses, curr_confidences, curr_attrs = [], [], []
    for hyp in hypotheses:
        confidence = DEFAULT_CONFIDENCE
        if len(hyp) and hyp[-1] not in [".", "?", "!"]:
            hyp += "."
            confidence = LOW_CONFIDENCE
        if hyp and confidence:
            curr_responses.append(hyp)
            curr_confidences.append(confidence)
            _curr_attrs = {
                "can_continue": CAN_NOT_CONTINUE,
                "skill_name": skill_name or "dff_universal_prompted_skill",
            }
            curr_attrs.append(_curr_attrs)
    return curr_responses, curr_confidences, curr_attrs


async def gather_responses(
    selected_skill_ids,
    skill_names,
    prompts,
    lm_service_urls,
    lm_service_configs,
    lm_service_kwargss,
    dialog_context,
    human_uttr_attributes,
):
    tasks = []
    async with aiohttp.ClientSession() as session:
        for skill_id in selected_skill_ids:
            skill_name = skill_names[skill_id]
            prompt = prompts[skill_id]
            lm_service_url = lm_service_urls[skill_id]
            lm_service_config = lm_service_configs[skill_id]
            lm_service_kwargs = lm_service_kwargss[skill_id]
            lm_service_timeout = (
                lm_service_config.pop("timeout", DEFAULT_LM_SERVICE_TIMEOUT)
                if lm_service_config
                else DEFAULT_LM_SERVICE_TIMEOUT
            )
            n_utterances_context = (
                lm_service_config.pop("n_utterances_context", N_UTTERANCES_CONTEXT)
                if lm_service_config
                else N_UTTERANCES_CONTEXT
            )

            tasks.append(
                asyncio.ensure_future(
                    async_request_to_prompted_generative_service(
                        session,
                        dialog_context[-n_utterances_context:],
                        prompt,
                        lm_service_url,
                        lm_service_config,
                        lm_service_timeout,
                        lm_service_kwargs,
                        skill_name,
                        human_uttr_attributes,
                    )
                )
            )
        responses, confidences, attrs = [], [], []
        for curr_responses, curr_confidences, curr_attrs in await asyncio.gather(*tasks):
            responses.extend(curr_responses)
            confidences.extend(curr_confidences)
            attrs.extend(curr_attrs)
        return responses, confidences, attrs


def generative_response(ctx: Context, actor: Actor, *args, **kwargs) -> Any:
    dialog_context = compose_data_for_model(ctx, actor)
    human_uttr_attributes = int_ctx.get_last_human_utterance(ctx, actor).get("attributes", {})
    # skill selector selects by display names!
    selected_skill_names = int_ctx.get_last_human_utterance(ctx, actor).get("annotations", {}).get("skill_selector", [])
    _skills = human_uttr_attributes.get("skills", [])

    skill_names = [skill["name"] for skill in _skills]
    if human_uttr_attributes.get("selected_skills", None) in ["all", []] or "prompt" not in human_uttr_attributes.get(
        "skill_selector", {}
    ):
        selected_skill_ids = [skill_id for skill_id, _ in enumerate(skill_names)]
    else:
        # if user do not ask to turn on all skills, turn on only skills selected by Skill Selector
        selected_skill_ids = [
            skill_id for skill_id, skill_name in enumerate(skill_names) if skill_name in selected_skill_names
        ]

    prompts = [skill.get("prompt", DEFAULT_PROMPT) for skill in _skills]
    lm_services = [skill.get("lm_service", {}) for skill in _skills]
    lm_service_urls = [lm_service.get("url", DEFAULT_LM_SERVICE_URL) for lm_service in lm_services]
    lm_service_configs = [lm_service.get("config", None) for lm_service in lm_services]
    lm_service_configs = [None for _ in prompts] if lm_service_configs is None else lm_service_configs
    lm_service_kwargss = [lm_service.get("kwargs", None) for lm_service in lm_services]
    lm_service_kwargss = [None for _ in prompts] if lm_service_kwargss is None else lm_service_kwargss
    lm_service_kwargss = [{} if el is None else el for el in lm_service_kwargss]

    if len(dialog_context) == 0:
        return ""

    responses, confidences, attrs = asyncio.run(
        gather_responses(
            selected_skill_ids,
            skill_names,
            prompts,
            lm_service_urls,
            lm_service_configs,
            lm_service_kwargss,
            dialog_context,
            human_uttr_attributes,
        )
    )

    if len(responses) == 0:
        return ""

    return int_rsp.multi_response(
        replies=responses,
        confidences=confidences,
        human_attr=[{} for _ in responses],
        bot_attr=[{} for _ in responses],
        hype_attr=attrs,
    )(ctx, actor, *args, **kwargs)
