import json
from os import getenv
import re
import sentry_sdk
import logging

from df_engine.core import Context, Actor
import common.dff.integration.context as int_ctx
from common.containers import get_envvars_for_llm
from common.prompts import send_request_to_prompted_generative_service, compose_sending_variables


API_CONFIGS = getenv("API_CONFIGS", None)
API_CONFIGS = [] if API_CONFIGS is None else API_CONFIGS.split(",")
api_conf = {}
for config in API_CONFIGS:
    with open(f"api_configs/{config}", "r") as f:
        conf = json.load(f)
        api_conf.update(conf)

GENERATIVE_SERVICE_CONFIG = getenv("GENERATIVE_SERVICE_CONFIG", "openai-chatgpt.json")
if GENERATIVE_SERVICE_CONFIG:
    with open(f"common/generative_configs/{GENERATIVE_SERVICE_CONFIG}", "r") as f:
        GENERATIVE_SERVICE_CONFIG = json.load(f)

GENERATIVE_TIMEOUT = float(getenv("GENERATIVE_TIMEOUT", 30))
GENERATIVE_TIMEOUT = (
    GENERATIVE_SERVICE_CONFIG.pop("timeout", GENERATIVE_TIMEOUT) if GENERATIVE_SERVICE_CONFIG else GENERATIVE_TIMEOUT
)

N_UTTERANCES_CONTEXT = int(getenv("N_UTTERANCES_CONTEXT", 1))
N_UTTERANCES_CONTEXT = (
    GENERATIVE_SERVICE_CONFIG.pop("n_utterances_context", N_UTTERANCES_CONTEXT)
    if GENERATIVE_SERVICE_CONFIG
    else N_UTTERANCES_CONTEXT
)
FIX_PUNCTUATION = re.compile(r"\s(?=[\.,:;])")
GENERATIVE_SERVICE_URL = getenv("GENERATIVE_SERVICE_URL", "http://openai-api-chatgpt:8145/respond")
ENVVARS_TO_SEND = get_envvars_for_llm(GENERATIVE_SERVICE_URL)


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
        plan = shared_memory.get("plan", list())
        step = shared_memory.get("step", 0)
        subtask_results = shared_memory.get("subtask_results", {})
        question = shared_memory.get("question", "")
        answer = ctx.misc.get("slots", {}).get("details_answer", None)
        api2use = shared_memory.get("api2use", "generative_lm")
        input_template = api_conf[api2use]["input_template"]
        dialog_context = list()
        if subtask_results:
            tasks_history = f"""Here is the story of completed tasks and results:
{subtask_results}
"""
        else:
            tasks_history = ""
        if question and answer:
            prompt = (
                tasks_history
                + f"""YOUR CURRENT TASK: {plan[step]}
CLARIFYING QUESTION TO THE USER: {question}
ANSWER TO THE QUESTION: {answer}
Form an input to the {api2use} tool, taking all info above into account. \
Input format: {input_template}"""
            )
        else:
            prompt = (
                tasks_history
                + f"""YOUR GOAL: {plan[step]}
Form an input to the {api2use} tool to achieve the goal. \
Input format: {input_template}"""
            )
        human_uttr_attributes = int_ctx.get_last_human_utterance(ctx, actor).get("attributes", {})
        sending_variables = compose_sending_variables(
            {},
            ENVVARS_TO_SEND,
            human_uttr_attributes,
        )
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
            api_input = ""
        logger.info(f"API INPUT: {api_input}")
        int_ctx.save_to_shared_memory(ctx, actor, api_input=api_input)
        int_ctx.save_to_shared_memory(ctx, actor, question="")
        int_ctx.save_to_shared_memory(ctx, actor, answer="")
        return api_input
