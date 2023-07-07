import json
from os import getenv
import re
import sentry_sdk
import logging

from df_engine.core import Context, Actor
import common.dff.integration.context as int_ctx
from common.prompts import send_request_to_prompted_generative_service, compose_sending_variables


API_CONFIGS = getenv("API_CONFIGS", None)
API_CONFIGS = [] if API_CONFIGS is None else API_CONFIGS.split(",")
api_conf = {}
for config in API_CONFIGS:
    with open(f"api_configs/{config}", "r") as f:
        conf = json.load(f)
        api_conf.update(conf)

N_UTTERANCES_CONTEXT = int(getenv("N_UTTERANCES_CONTEXT", 1))
FIX_PUNCTUATION = re.compile(r"\s(?=[\.,:;])")
ENVVARS_TO_SEND = getenv("ENVVARS_TO_SEND", None)
ENVVARS_TO_SEND = [] if ENVVARS_TO_SEND is None else ENVVARS_TO_SEND.split(",")
GENERATIVE_SERVICE_URL = getenv("GENERATIVE_SERVICE_URL", "http://openai-api-chatgpt:8145/respond")
GENERATIVE_SERVICE_CONFIG = getenv("GENERATIVE_SERVICE_CONFIG", "openai-chatgpt.json")
if GENERATIVE_SERVICE_CONFIG:
    with open(f"common/generative_configs/{GENERATIVE_SERVICE_CONFIG}", "r") as f:
        GENERATIVE_SERVICE_CONFIG = json.load(f)
GENERATIVE_TIMEOUT = int(getenv("GENERATIVE_TIMEOUT", 30))


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def compose_data_for_model(ctx, actor):
    # consider N_UTTERANCES_CONTEXT last utterances
    context = int_ctx.get_utterances(ctx, actor)[-N_UTTERANCES_CONTEXT:]
    context = [uttr.get("text", "") for uttr in context]

    if context:
        context = [re.sub(FIX_PUNCTUATION, "", x) for x in context]
    return context


def compose_input_for_API(ctx: Context, actor: Actor, *args, **kwargs):
    if not ctx.validation:
        shared_memory = int_ctx.get_shared_memory(ctx, actor)
        thought = shared_memory.get("thought", None)
        question = shared_memory.get("question", None)
        answer = ctx.misc.get("slots", {}).get("details_answer", None)
        api2use = shared_memory.get("api2use", "generative_lm")
        input_template = api_conf[api2use]["input_template"]
        dialog_context = compose_data_for_model(ctx, actor)
        if question and answer:
            prompt = f"""YOUR GOAL: {thought}
CLARIFYING QUESTION TO THE USER: {question}
ANSWER TO THE QUESTION: {answer}
Form an input to the {api2use} tool, taking all info above into account. \
Input format: {input_template}"""
        else:
            prompt = f"""YOUR GOAL: {thought}
Form an input to the {api2use} tool to achieve the goal. \
Input format: {input_template}"""
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
                api_input = hypotheses[0]
            except Exception as e:
                sentry_sdk.capture_exception(e)
                logger.exception(e)
                api_input = None
        else:
            api_input = None
        logger.info(f"API INPUT: {api_input}")
        int_ctx.save_to_shared_memory(ctx, actor, api_input=api_input)
        int_ctx.save_to_shared_memory(ctx, actor, question=None)
        int_ctx.save_to_shared_memory(ctx, actor, answer=None)
        return api_input
