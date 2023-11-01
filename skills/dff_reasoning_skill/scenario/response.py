import logging
import sentry_sdk
import json
import re
from os import getenv
import time
import signal
from datetime import date

from df_engine.core import Context, Actor
import common.dff.integration.context as int_ctx
from common.containers import get_envvars_for_llm, is_container_running
from common.prompts import send_request_to_prompted_generative_service, compose_sending_variables

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

while True:
    result = is_container_running(GENERATIVE_SERVICE_URL)
    if result:
        logger.info(f"GENERATIVE_SERVICE_URL: {GENERATIVE_SERVICE_URL} is ready")
        break
    else:
        time.sleep(5)
        continue

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
TIME_SLEEP = float(getenv("TIME_SLEEP", 0))

FIX_PUNCTUATION = re.compile(r"\s(?=[\.,:;])")
DEFAULT_CONFIDENCE = 0.9
LOW_CONFIDENCE = 0.7

ENVVARS_TO_SEND = get_envvars_for_llm(GENERATIVE_SERVICE_URL)
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


def timeout_handler(signum, frame):
    assert signum
    assert frame
    raise Exception("API timeout")


def planning(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    plan = list()
    if not ctx.validation:
        today = date.today()
        api_desc = {}
        for key, value in api_conf.items():
            api_desc[key] = value["description"]
        prompt = f"""Today date is: {today}. You received the following user request: {ctx.last_request}

You have the following tools available:
{api_desc}

Your Task:
Think about how to handle this user request and split the request into subtasks.

Return the list of subtasks in the following format:

PLAN:
1. Subtask 1
2. Subtask 2
3. Subtask 3
...
    """
        dialog_context = list()
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
            plan = hypotheses[0]
            plan = plan.split("\n")[1:]
        except Exception as e:
            sentry_sdk.capture_exception(e)
            logger.exception(e)
            plan = list()
        int_ctx.save_to_shared_memory(ctx, actor, plan=plan)
        int_ctx.save_to_shared_memory(ctx, actor, step=0)
        int_ctx.save_to_shared_memory(ctx, actor, user_request=ctx.last_request)
        logger.info(f"PLAN: {plan}")
        time.sleep(TIME_SLEEP)
    return plan


def check_if_needs_details(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    answer = ""
    if not ctx.validation:
        shared_memory = int_ctx.get_shared_memory(ctx, actor)
        plan = shared_memory.get("plan", list())
        step = shared_memory.get("step", 0)
        subtask_results = shared_memory.get("subtask_results", {})
        if plan:
            if subtask_results:
                tasks_history = f"""Here is the story of completed tasks and results:
    {subtask_results}
    """
            else:
                tasks_history = ""
            prompt = f"""{tasks_history}Here is your current task:
{plan[step]}
Do you need to clarify any details with the user related to your current task? \
ANSWER ONLY YES/NO"""
            dialog_context = list()
            human_uttr_attributes = int_ctx.get_last_human_utterance(ctx, actor).get("attributes", {})
            envvars_to_send = (
                ENVVARS_TO_SEND if len(ENVVARS_TO_SEND) else human_uttr_attributes.get("envvars_to_send", [])
            )
            sending_variables = compose_sending_variables(
                {},
                envvars_to_send,
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
                answer = hypotheses[0]
            except Exception as e:
                sentry_sdk.capture_exception(e)
                logger.exception(e)
                answer = ""
            logger.info(f"NEEDS_CLARIFICATION: {answer}")
            int_ctx.save_to_shared_memory(ctx, actor, needs_details=answer)
        else:
            answer = ""
    return answer


def clarify_details(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    question = ""
    if not ctx.validation:
        shared_memory = int_ctx.get_shared_memory(ctx, actor)
        plan = shared_memory.get("plan", list())
        step = shared_memory.get("step", 0)
        subtask_results = shared_memory.get("subtask_results", {})
        if subtask_results:
            tasks_history = f"""CONTEXT:
    {"---".join(list(subtask_results.values()))}
    """
        else:
            tasks_history = ""

        prompt = f"""{tasks_history}Here is your current task:
{plan[step]}
Formulate a clarifying question to the user to get necessary information \
to complete the current task"""
        dialog_context = list()
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
            question = hypotheses[0]
        except Exception as e:
            sentry_sdk.capture_exception(e)
            logger.exception(e)
            question = ""
        int_ctx.save_to_shared_memory(ctx, actor, question=question)
        logger.info(f"CLARIFYING QUESTION: {question}")
        time.sleep(TIME_SLEEP)
    return question


def choose_tool(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    api2use = ""
    if not ctx.validation:
        today = date.today()
        shared_memory = int_ctx.get_shared_memory(ctx, actor)
        plan = shared_memory.get("plan", list())
        step = shared_memory.get("step", 0)
        subtask_results = shared_memory.get("subtask_results", {})
        for key in api_conf.keys():
            if key in plan[step]:
                int_ctx.save_to_shared_memory(ctx, actor, api2use=key)
                return key
        api_desc = {}
        for key, value in api_conf.items():
            api_desc[key] = value["description"]

        if subtask_results:
            tasks_history = f"""CONTEXT:
    {"---".join(list(subtask_results.values()))}
    """
        else:
            tasks_history = ""
        prompt = f"""Today date is: {today}. {tasks_history}YOUR CURRENT TASK:
{plan[step]}
AVAILABLE TOOLS:
{api_desc}
Choose the best tool to use to complete your current task. \
Return the name of the best tool to use exactly as it is written in the dictionary. \
DON'T EXPLAIN YOUR DECISION, JUST RETURN THE KEY. E.g. google_api"""
        dialog_context = list()
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
            if hypotheses[0] in api_conf.keys():
                api2use = hypotheses[0]
            else:
                if any(key in hypotheses[0] for key in api_conf.keys()):
                    api2use = key

            assert api2use
        except Exception as e:
            sentry_sdk.capture_exception(e)
            logger.exception(e)
            api2use = "generative_lm"
        int_ctx.save_to_shared_memory(ctx, actor, api2use=api2use)
        logger.info(f"CHOSEN TOOL: {api2use}")
        time.sleep(TIME_SLEEP)
    return api2use


def ask4approval(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    response = ""
    if not ctx.validation:
        shared_memory = int_ctx.get_shared_memory(ctx, actor)
        api2use = shared_memory.get("api2use", "")
        response = f"""I need to use {api_conf[api2use]['display_name']} \
to handle your request. Do you approve?"""
    return response


def complete_subtask(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    response = ""
    if not ctx.validation:
        shared_memory = int_ctx.get_shared_memory(ctx, actor)
        api2use = shared_memory.get("api2use", "")
        subtask_results = shared_memory.get("subtask_results", {})
        step = shared_memory.get("step", 0)
        if api2use:
            timeout = api_conf[api2use]["timeout"]
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout)
            try:
                logger.info(f"api name: {api2use}")
                response = globals()[f"{api2use}_response"](ctx, actor)
            except Exception:
                response = "Unfortunately, something went wrong with API"
            signal.alarm(0)
        else:
            response = "Unfortunately, something went wrong"
        logger.info(f"subtask response: {response}")
        subtask_results[str(step)] = response
        logger.info(f"subtask result: {subtask_results}")
        int_ctx.save_to_shared_memory(ctx, actor, subtask_results=subtask_results)
    return response


def self_reflexion(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    response = ""
    if not ctx.validation:
        today = date.today()
        shared_memory = int_ctx.get_shared_memory(ctx, actor)
        subtask_results = shared_memory.get("subtask_results", {})
        plan = shared_memory.get("plan", list())
        step = shared_memory.get("step", 0)
        prompt = f"""Today date is: {today}. YOUR TASK: {plan[step]}
RESULT: {subtask_results[str(step)]}
Do you think that you completed the task and the result is good and relevant? Return 'Yes', if positive, \
and 'No' and the reason if negative."""
        dialog_context = list()
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
            response = hypotheses[0]
        except Exception as e:
            sentry_sdk.capture_exception(e)
            logger.exception(e)
            response = ""
        logger.info(f"self reflexion: {response}")
        step += 1
        int_ctx.save_to_shared_memory(ctx, actor, step=step)
        int_ctx.save_to_shared_memory(ctx, actor, self_reflexion=response)
    return response


def final_answer(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    response = ""
    if not ctx.validation:
        today = date.today()
        shared_memory = int_ctx.get_shared_memory(ctx, actor)
        subtask_results = shared_memory.get("subtask_results", {})
        user_request = shared_memory.get("user_request", "")
        prompt = f"""Today date is: {today}. USER REQUEST: {user_request}
CONTEXT:
{"---".join(list(subtask_results.values()))}
YOUR TASK: given the information in the context, form a final answer to the user request"""
        dialog_context = list()
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
            response = hypotheses[0]
        except Exception as e:
            sentry_sdk.capture_exception(e)
            logger.exception(e)
            response = ""

        subtask_results = {}
        plan = list()
        step = 0
        int_ctx.save_to_shared_memory(ctx, actor, subtask_results=subtask_results)
        int_ctx.save_to_shared_memory(ctx, actor, plan=plan)
        int_ctx.save_to_shared_memory(ctx, actor, step=step)
        logger.info(f"final answer: {response}")
    return response


def retry_task(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    response = ""
    if not ctx.validation:
        shared_memory = int_ctx.get_shared_memory(ctx, actor)
        subtask_results = shared_memory.get("subtask_results", {})
        plan = shared_memory.get("plan", list())
        step = shared_memory.get("step", 1)
        step -= 1
        del subtask_results[str(step)]
        int_ctx.save_to_shared_memory(ctx, actor, step=step)
        int_ctx.save_to_shared_memory(ctx, actor, subtask_results=subtask_results)
        response = f"""I didn't manage to complete subtask:\n{plan[step]}\nI will try again."""
    return response
