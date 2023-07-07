import logging
import sentry_sdk
import json
import re
from os import getenv
import time
import signal

from df_engine.core import Context, Actor
import common.dff.integration.context as int_ctx
from common.prompts import send_request_to_prompted_generative_service, compose_sending_variables
from scenario.utils import compose_data_for_model


from scenario.api_responses.generative_lm import generative_lm_response
from scenario.api_responses.news_api import news_api_response
from scenario.api_responses.wolframalpha_api import wolframalpha_api_response
from scenario.api_responses.google_api import google_api_response
from scenario.api_responses.weather_api import weather_api_response

assert generative_lm_response
assert news_api_response
assert wolframalpha_api_response
assert google_api_response
assert weather_api_response


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

GENERATIVE_SERVICE_URL = getenv("GENERATIVE_SERVICE_URL", "http://openai-api-chatgpt:8145/respond")
GENERATIVE_SERVICE_CONFIG = getenv("GENERATIVE_SERVICE_CONFIG", "openai-chatgpt.json")
if GENERATIVE_SERVICE_CONFIG:
    with open(f"common/generative_configs/{GENERATIVE_SERVICE_CONFIG}", "r") as f:
        GENERATIVE_SERVICE_CONFIG = json.load(f)
GENERATIVE_TIMEOUT = int(getenv("GENERATIVE_TIMEOUT", 30))
N_UTTERANCES_CONTEXT = int(getenv("N_UTTERANCES_CONTEXT", 1))

FIX_PUNCTUATION = re.compile(r"\s(?=[\.,:;])")
DEFAULT_CONFIDENCE = 0.9
LOW_CONFIDENCE = 0.7

ENVVARS_TO_SEND = getenv("ENVVARS_TO_SEND", None)
ENVVARS_TO_SEND = [] if ENVVARS_TO_SEND is None else ENVVARS_TO_SEND.split(",")
available_variables = {f"{var}": getenv(var, None) for var in ENVVARS_TO_SEND}

API_CONFIGS = getenv("API_CONFIGS", None)
API_CONFIGS = [] if API_CONFIGS is None else API_CONFIGS.split(",")
api_conf = {}
for config in API_CONFIGS:
    with open(f"api_configs/{config}", "r") as f:
        conf = json.load(f)
        api_conf.update(conf)


for key, value in api_conf.copy().items():
    for api_key in value["keys"]:
        if not available_variables[api_key]:
            del api_conf[key]
            break

logger.info(f"Available APIs: {', '.join([api['display_name'] for api in api_conf.values()])}")


def timeout_handler():
    raise Exception("API timeout")


def thought(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    if not ctx.validation:
        shared_memory = int_ctx.get_shared_memory(ctx, actor)
        thought = shared_memory.get("thought", None)
        prompt = f"""You received the following user request:
{ctx.last_request}
Think about what do you need to do to handle this request. \
Return your thought in one sentence"""

        dialog_context = compose_data_for_model(ctx, actor)
        human_uttr_attributes = int_ctx.get_last_human_utterance(ctx, actor).get("attributes", {})
        lm_service_kwargs = human_uttr_attributes.pop("lm_service_kwargs", None)
        lm_service_kwargs = {} if lm_service_kwargs is None else lm_service_kwargs
        envvars_to_send = ENVVARS_TO_SEND if len(ENVVARS_TO_SEND) else human_uttr_attributes.get("envvars_to_send", [])
        sending_variables = compose_sending_variables(
            lm_service_kwargs,
            envvars_to_send,
            **human_uttr_attributes,
        )
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
                thought = hypotheses[0]
            except Exception as e:
                sentry_sdk.capture_exception(e)
                logger.exception(e)
                thought = None
        else:
            thought = None
        int_ctx.save_to_shared_memory(ctx, actor, thought=thought)
        logger.info(f"THOUGHT: {thought}")
        time.sleep(5)
        return thought


def check_if_needs_details(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    if not ctx.validation:
        shared_memory = int_ctx.get_shared_memory(ctx, actor)
        thought = shared_memory.get("thought", None)
        answer = shared_memory.get("needs_details", None)
        prompt = f"""Here is your goal:
{thought}
Do you need to clarify any details with the user? \
ANSWER ONLY YES/NO"""
        dialog_context = compose_data_for_model(ctx, actor)
        human_uttr_attributes = int_ctx.get_last_human_utterance(ctx, actor).get("attributes", {})
        lm_service_kwargs = human_uttr_attributes.pop("lm_service_kwargs", None)
        lm_service_kwargs = {} if lm_service_kwargs is None else lm_service_kwargs
        envvars_to_send = ENVVARS_TO_SEND if len(ENVVARS_TO_SEND) else human_uttr_attributes.get("envvars_to_send", [])
        sending_variables = compose_sending_variables(
            lm_service_kwargs,
            envvars_to_send,
            **human_uttr_attributes,
        )
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
                answer = hypotheses[0]
            except Exception as e:
                sentry_sdk.capture_exception(e)
                logger.exception(e)
                answer = None
        else:
            answer = None
        logger.info(f"NEEDS_CLARIFICATION: {answer}")
        int_ctx.save_to_shared_memory(ctx, actor, needs_details=answer)
        return answer


def clarify_details(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    if not ctx.validation:
        shared_memory = int_ctx.get_shared_memory(ctx, actor)
        thought = shared_memory.get("thought", None)
        question = shared_memory.get("question", None)
        prompt = f"""Here is your goal:
{thought}
Formulate a clarifying question to the user to get necessary information \
to complete the task"""
        dialog_context = compose_data_for_model(ctx, actor)
        human_uttr_attributes = int_ctx.get_last_human_utterance(ctx, actor).get("attributes", {})
        lm_service_kwargs = human_uttr_attributes.pop("lm_service_kwargs", None)
        lm_service_kwargs = {} if lm_service_kwargs is None else lm_service_kwargs
        envvars_to_send = ENVVARS_TO_SEND if len(ENVVARS_TO_SEND) else human_uttr_attributes.get("envvars_to_send", [])
        sending_variables = compose_sending_variables(
            lm_service_kwargs,
            envvars_to_send,
            **human_uttr_attributes,
        )
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
                question = hypotheses[0]
            except Exception as e:
                sentry_sdk.capture_exception(e)
                logger.exception(e)
                question = None
        else:
            question = None
        int_ctx.save_to_shared_memory(ctx, actor, question=question)
        logger.info(f"CLARIFYING QUESTION: {question}")
        time.sleep(5)
        return question


def response_with_chosen_api(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    if not ctx.validation:
        shared_memory = int_ctx.get_shared_memory(ctx, actor)
        thought = shared_memory.get("thought", None)
        api2use = shared_memory.get("api2use", None)
        api_desc = {}
        for key, value in api_conf.items():
            api_desc[key] = value["description"]
        prompt = f"""YOUR GOAL:
{thought}
AVAILABLE TOOLS:
{api_desc}
Choose the best tool to use to complete your task. \
Return the name of the best tool to use exactly as it is written in the dictionary. \
DON'T EXPLAIN YOUR DECISION, JUST RETURN THE KEY. E.g. google_api"""
        dialog_context = compose_data_for_model(ctx, actor)
        human_uttr_attributes = int_ctx.get_last_human_utterance(ctx, actor).get("attributes", {})
        lm_service_kwargs = human_uttr_attributes.pop("lm_service_kwargs", None)
        lm_service_kwargs = {} if lm_service_kwargs is None else lm_service_kwargs
        envvars_to_send = ENVVARS_TO_SEND if len(ENVVARS_TO_SEND) else human_uttr_attributes.get("envvars_to_send", [])
        sending_variables = compose_sending_variables(
            lm_service_kwargs,
            envvars_to_send,
            **human_uttr_attributes,
        )
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
                try:
                    if api_conf[hypotheses[0]]["needs_approval"] == "False":
                        api2use = hypotheses[0]
                        int_ctx.save_to_shared_memory(ctx, actor, api2use=api2use)
                        timeout = api_conf[api2use]["timeout"]
                        signal.signal(signal.SIGALRM, timeout_handler)
                        signal.alarm(timeout)
                        try:
                            response = globals()[f"{api2use}_response"](ctx, actor)
                        except Exception:
                            response = "Unfortunately, somthing went wrong with API"
                        signal.alarm(0)
                    else:
                        api2use = hypotheses[0]
                        int_ctx.save_to_shared_memory(ctx, actor, api2use=api2use)
                        response = f"""I need to use {api_conf[api2use]['display_name']} \
to handle your request. Do you approve?"""
                except KeyError:
                    for key in api_conf.keys():
                        if key in hypotheses[0]:
                            if api_conf[key]["needs_approval"] == "False":
                                api2use = key
                                int_ctx.save_to_shared_memory(ctx, actor, api2use=api2use)
                                timeout = api_conf[api2use]["timeout"]
                                signal.signal(signal.SIGALRM, timeout_handler)
                                signal.alarm(timeout)
                                try:
                                    response = globals()[f"{api2use}_response"](ctx, actor)
                                except Exception:
                                    response = "Unfortunately, somthing went wrong with API"
                                signal.alarm(0)
                            else:
                                api2use = key
                                int_ctx.save_to_shared_memory(ctx, actor, api2use=api2use)
                                response = f"""I need to use {api2use} to handle your request. Do you approve?"""
                            break

            except KeyError:
                api2use = "generative_lm"
                int_ctx.save_to_shared_memory(ctx, actor, api2use=api2use)
                response = globals()[f"{api2use}_response"](ctx, actor)
        else:
            response = None

        try:
            return response
        except UnboundLocalError:
            api2use = "generative_lm"
            int_ctx.save_to_shared_memory(ctx, actor, api2use=api2use)
            response = globals()[f"{api2use}_response"](ctx, actor)
            return response


def response_with_approved_api(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    if not ctx.validation:
        shared_memory = int_ctx.get_shared_memory(ctx, actor)
        api2use = shared_memory.get("api2use", None)
        timeout = api_conf[api2use]["timeout"]
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
        try:
            response = globals()[f"{api2use}_response"](ctx, actor)
        except Exception:
            response = "Unfortunately, somthing went wrong with API"
        signal.alarm(0)
        return response
