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
GENERATIVE_TIMEOUT = int(getenv("GENERATIVE_TIMEOUT", 120))
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


def plan(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    if not ctx.validation:
        api_desc = {}
        for key, value in api_conf.items():
            api_desc[key] = value["description"]
        prompt = f"""You received the following user request: {ctx.last_request}
You have the following tools available:
{api_desc}
Think about what do you need to do to handle this request. \
Break the request into subtasks. Return the list of subtasks in the following format:
PLAN:\n1. Subtask 1\n2. Subtask 2\n..."""
        dialog_context = []
        human_uttr_attributes = int_ctx.get_last_human_utterance(ctx, actor).get("attributes", {})
        lm_service_kwargs = human_uttr_attributes.pop("lm_service_kwargs", None)
        lm_service_kwargs = {} if lm_service_kwargs is None else lm_service_kwargs
        envvars_to_send = ENVVARS_TO_SEND if len(ENVVARS_TO_SEND) else human_uttr_attributes.get("envvars_to_send", [])
        sending_variables = compose_sending_variables(
            lm_service_kwargs,
            envvars_to_send,
            **human_uttr_attributes,
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
            plan = None
        int_ctx.save_to_shared_memory(ctx, actor, plan=plan)
        int_ctx.save_to_shared_memory(ctx, actor, step=0)
        int_ctx.save_to_shared_memory(ctx, actor, user_request=ctx.last_request)
        logger.info(f"PLAN: {plan}")
        time.sleep(5)
        return plan


def check_if_needs_details(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    if not ctx.validation:
        shared_memory = int_ctx.get_shared_memory(ctx, actor)
        plan = shared_memory.get("plan", [])
        step = shared_memory.get("step", 0)
        subtask_results = shared_memory.get("subtask_results", {})
        if plan:
            if subtask_results:
                tasks_history = f"""Here is the story of completed tasks and results:
{subtask_results}
"""
            else:
                tasks_history = ""
            prompt = (
                tasks_history
                + f"""Here is your current task:
{plan[step]}
Do you need to clarify any details with the user related to your current task? \
ANSWER ONLY YES/NO"""
            )
            dialog_context = []
            human_uttr_attributes = int_ctx.get_last_human_utterance(ctx, actor).get("attributes", {})
            lm_service_kwargs = human_uttr_attributes.pop("lm_service_kwargs", None)
            lm_service_kwargs = {} if lm_service_kwargs is None else lm_service_kwargs
            envvars_to_send = (
                ENVVARS_TO_SEND if len(ENVVARS_TO_SEND) else human_uttr_attributes.get("envvars_to_send", [])
            )
            sending_variables = compose_sending_variables(
                lm_service_kwargs,
                envvars_to_send,
                **human_uttr_attributes,
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
                answer = None
            logger.info(f"NEEDS_CLARIFICATION: {answer}")
            int_ctx.save_to_shared_memory(ctx, actor, needs_details=answer)
        return answer


def clarify_details(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    if not ctx.validation:
        shared_memory = int_ctx.get_shared_memory(ctx, actor)
        plan = shared_memory.get("plan", [])
        step = shared_memory.get("step", 0)
        subtask_results = shared_memory.get("subtask_results", {})
        if subtask_results:
            tasks_history = f"""CONTEXT:
{"---".join(list(subtask_results.values()))}
"""
        else:
            tasks_history = ""

        prompt = (
            tasks_history
            + f"""Here is your current task:
{plan[step]}
Formulate a clarifying question to the user to get necessary information \
to complete the current task"""
        )
        dialog_context = []
        human_uttr_attributes = int_ctx.get_last_human_utterance(ctx, actor).get("attributes", {})
        lm_service_kwargs = human_uttr_attributes.pop("lm_service_kwargs", None)
        lm_service_kwargs = {} if lm_service_kwargs is None else lm_service_kwargs
        envvars_to_send = ENVVARS_TO_SEND if len(ENVVARS_TO_SEND) else human_uttr_attributes.get("envvars_to_send", [])
        sending_variables = compose_sending_variables(
            lm_service_kwargs,
            envvars_to_send,
            **human_uttr_attributes,
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
            question = None
        int_ctx.save_to_shared_memory(ctx, actor, question=question)
        logger.info(f"CLARIFYING QUESTION: {question}")
        time.sleep(5)
        return question


def choose_tool(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    if not ctx.validation:
        shared_memory = int_ctx.get_shared_memory(ctx, actor)
        plan = shared_memory.get("plan", [])
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
        prompt = (
            tasks_history
            + f"""YOUR CURRENT TASK:
{plan[step]}
AVAILABLE TOOLS:
{api_desc}
Choose the best tool to use to complete your current task. \
Return the name of the best tool to use exactly as it is written in the dictionary. \
DON'T EXPLAIN YOUR DECISION, JUST RETURN THE KEY. E.g. google_api"""
        )
        dialog_context = []
        human_uttr_attributes = int_ctx.get_last_human_utterance(ctx, actor).get("attributes", {})
        lm_service_kwargs = human_uttr_attributes.pop("lm_service_kwargs", None)
        lm_service_kwargs = {} if lm_service_kwargs is None else lm_service_kwargs
        envvars_to_send = ENVVARS_TO_SEND if len(ENVVARS_TO_SEND) else human_uttr_attributes.get("envvars_to_send", [])
        sending_variables = compose_sending_variables(
            lm_service_kwargs,
            envvars_to_send,
            **human_uttr_attributes,
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
                for key in api_conf.keys():
                    if key in hypotheses[0]:
                        api2use = key

            assert api2use
        except Exception as e:
            sentry_sdk.capture_exception(e)
            logger.exception(e)
            api2use = "generative_lm"
        int_ctx.save_to_shared_memory(ctx, actor, api2use=api2use)
        logger.info(f"CHOSEN TOOL: {api2use}")
        time.sleep(5)
        return api2use


def ask4approval(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    if not ctx.validation:
        shared_memory = int_ctx.get_shared_memory(ctx, actor)
        api2use = shared_memory.get("api2use", None)
        response = f"""I need to use {api_conf[api2use]['display_name']} \
to handle your request. Do you approve?"""
        return response


def complete_subtask(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    if not ctx.validation:
        shared_memory = int_ctx.get_shared_memory(ctx, actor)
        api2use = shared_memory.get("api2use", None)
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
        logger.info(f"subtask response: {response}")
        subtask_results[str(step)] = response
        logger.info(f"subtask result: {subtask_results}")
        int_ctx.save_to_shared_memory(ctx, actor, subtask_results=subtask_results)
        return response


def self_reflexion(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    if not ctx.validation:
        shared_memory = int_ctx.get_shared_memory(ctx, actor)
        subtask_results = shared_memory.get("subtask_results", {})
        plan = shared_memory.get("plan", [])
        step = shared_memory.get("step", 0)
        prompt = f"""YOUR TASK: {plan[step]}
RESULT: {subtask_results[str(step)]}
Do you think that you completed the task and the result is good and relevant? Return 'Yes', if positive, \
and 'No' and the reason if negative."""
        dialog_context = []
        human_uttr_attributes = int_ctx.get_last_human_utterance(ctx, actor).get("attributes", {})
        lm_service_kwargs = human_uttr_attributes.pop("lm_service_kwargs", None)
        lm_service_kwargs = {} if lm_service_kwargs is None else lm_service_kwargs
        envvars_to_send = ENVVARS_TO_SEND if len(ENVVARS_TO_SEND) else human_uttr_attributes.get("envvars_to_send", [])
        sending_variables = compose_sending_variables(
            lm_service_kwargs,
            envvars_to_send,
            **human_uttr_attributes,
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
            response = None
        logger.info(f"self reflexion: {response}")
        step += 1
        int_ctx.save_to_shared_memory(ctx, actor, step=step)
        int_ctx.save_to_shared_memory(ctx, actor, self_reflexion=response)
        return response


def final_answer(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    if not ctx.validation:
        shared_memory = int_ctx.get_shared_memory(ctx, actor)
        subtask_results = shared_memory.get("subtask_results", {})
        user_request = shared_memory.get("user_request", "")
        prompt = f"""USER REQUEST: {user_request}
CONTEXT:
{"---".join(list(subtask_results.values()))}
YOUR TASK: given the information in the context, form a final answer to the user request"""
        dialog_context = []
        human_uttr_attributes = int_ctx.get_last_human_utterance(ctx, actor).get("attributes", {})
        lm_service_kwargs = human_uttr_attributes.pop("lm_service_kwargs", None)
        lm_service_kwargs = {} if lm_service_kwargs is None else lm_service_kwargs
        envvars_to_send = ENVVARS_TO_SEND if len(ENVVARS_TO_SEND) else human_uttr_attributes.get("envvars_to_send", [])
        sending_variables = compose_sending_variables(
            lm_service_kwargs,
            envvars_to_send,
            **human_uttr_attributes,
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
            response = None

        subtask_results = {}
        plan = []
        step = 0
        int_ctx.save_to_shared_memory(ctx, actor, subtask_results=subtask_results)
        int_ctx.save_to_shared_memory(ctx, actor, plan=plan)
        int_ctx.save_to_shared_memory(ctx, actor, step=step)
        logger.info(f"final answer: {response}")
        return response


def recomplete_task(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    if not ctx.validation:
        shared_memory = int_ctx.get_shared_memory(ctx, actor)
        subtask_results = shared_memory.get("subtask_results", {})
        plan = shared_memory.get("plan", [])
        step = shared_memory.get("step", 0)
        step -= 1
        del subtask_results[str(step)]
        int_ctx.save_to_shared_memory(ctx, actor, step=step)
        int_ctx.save_to_shared_memory(ctx, actor, subtask_results=subtask_results)
        response = f"""I didn't manage to complete subtask:\n{plan[step]}\nI will try again."""
        return response


def revise_plan(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    if not ctx.validation:
        shared_memory = int_ctx.get_shared_memory(ctx, actor)
        subtask_results = shared_memory.get("subtask_results", {})
        plan = shared_memory.get("plan", [])
        step = shared_memory.get("step", 0)
        step -= 1
        user_request = shared_memory.get("user_request", "")
        self_reflexion = shared_memory.get("self_reflexion", "")
        prompt = f"""USER REQUEST: {user_request}
PLAN YOU HAD TO COMPLETE IT: {plan}
RESULTS OF EACH SUBTASK IN A PLAN: {"---".join(list(subtask_results.values()))}
DID YOU MANAGE TO COMPLETE {plan[step]}? -- {self_reflexion}
YOUR TASK: revise the plan and fix it. Don't change those subtasks that don't have to be changed. \
Return only the revised plan in the following format: 'PLAN:\n1. Subtask 1\n2. Subtask 2\n...'"""
        dialog_context = []
        human_uttr_attributes = int_ctx.get_last_human_utterance(ctx, actor).get("attributes", {})
        lm_service_kwargs = human_uttr_attributes.pop("lm_service_kwargs", None)
        lm_service_kwargs = {} if lm_service_kwargs is None else lm_service_kwargs
        envvars_to_send = ENVVARS_TO_SEND if len(ENVVARS_TO_SEND) else human_uttr_attributes.get("envvars_to_send", [])
        sending_variables = compose_sending_variables(
            lm_service_kwargs,
            envvars_to_send,
            **human_uttr_attributes,
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
            revised_plan = hypotheses[0]
            revised_plan = revised_plan.split("\n")[1:]
        except Exception as e:
            sentry_sdk.capture_exception(e)
            logger.exception(e)
            revised_plan = None
            
        logger.info(f"REVISED PLAN: {revised_plan}")
        for i, subtask in enumerate(revised_plan):
            try:
                if subtask != plan[i]:
                    step = i
                    break
            except Exception as e:
                sentry_sdk.capture_exception(e)
                logger.exception(e)
        
        if len(subtask_results) > 0:
            for i in range(step, len(subtask_results)):
                del subtask_results[str(step)]
        
        int_ctx.save_to_shared_memory(ctx, actor, step=step)
        int_ctx.save_to_shared_memory(ctx, actor, plan=revised_plan)
        int_ctx.save_to_shared_memory(ctx, actor, subtask_results=subtask_results)
        return f"""Original plan: {plan}\nRevised plan: {revised_plan}"""

                




