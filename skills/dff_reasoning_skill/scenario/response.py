import logging
import sentry_sdk
import json
import re
import requests
from os import getenv
from typing import Any
import time
import wolframalpha
import signal

from langchain.agents import Tool
from langchain.memory import ConversationBufferMemory
from langchain import OpenAI
from langchain.utilities import GoogleSearchAPIWrapper
from langchain.agents import initialize_agent

from df_engine.core import Context, Actor
import common.dff.integration.context as int_ctx
import common.dff.integration.response as int_rsp
from common.constants import CAN_NOT_CONTINUE
from common.prompts import send_request_to_prompted_generative_service, compose_sending_variables

from tools.city_slot import OWMCitySlot
from tools.weather_service import weather_forecast_now

CITY_SLOT = OWMCitySlot()


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
API_CONFIG = getenv("API_CONFIG", "api_conf.json")

FIX_PUNCTUATION = re.compile(r"\s(?=[\.,:;])")
DEFAULT_CONFIDENCE = 0.9
LOW_CONFIDENCE = 0.7

ENVVARS_TO_SEND = getenv("ENVVARS_TO_SEND", None)
ENVVARS_TO_SEND = [] if ENVVARS_TO_SEND is None else ENVVARS_TO_SEND.split(",")
available_variables = {f"{var}": getenv(var, None) for var in ENVVARS_TO_SEND}

with open(f"api_configs/{API_CONFIG}", "r") as f:
    api_conf = json.load(f)

for key, value in api_conf.copy().items():
    for api_key in value["keys"]:
        if not available_variables[api_key]:
            del api_conf[key]
            break

logger.info(f"Available APIs: {', '.join([api['display_name'] for api in api_conf.values()])}")


if "google_api" in api_conf.keys():
    search = GoogleSearchAPIWrapper()
    tools = [
        Tool(
            name="Current Search",
            func=search.run,
            description="useful when you need to answer questions about current \
events or the current state of the world",
        ),
    ]
    memory = ConversationBufferMemory(memory_key="chat_history")
    llm = OpenAI(temperature=0)
    agent_chain = initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=True, memory=memory)


def timeout_handler():
    raise Exception("API timeout")


def google_api_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    if not ctx.validation:
        api_input = compose_input_for_API(ctx, actor)
        answer = agent_chain.run(api_input)
        return answer


def compose_data_for_model(ctx, actor):
    # consider N_UTTERANCES_CONTEXT last utterances
    context = int_ctx.get_utterances(ctx, actor)[-N_UTTERANCES_CONTEXT:]
    context = [uttr.get("text", "") for uttr in context]

    if context:
        context = [re.sub(FIX_PUNCTUATION, "", x) for x in context]
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
    human_uttr_attributes = int_ctx.get_last_human_utterance(ctx, actor).get("attributes", {})
    lm_service_kwargs = human_uttr_attributes.pop("lm_service_kwargs", None)
    lm_service_kwargs = {} if lm_service_kwargs is None else lm_service_kwargs
    envvars_to_send = ENVVARS_TO_SEND if len(ENVVARS_TO_SEND) else human_uttr_attributes.get("envvars_to_send", [])
    sending_variables = compose_sending_variables(
        lm_service_kwargs,
        envvars_to_send,
        **human_uttr_attributes,
    )
    prompt = compose_input_for_API(ctx, actor)
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


def weather_api_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    api_input = compose_input_for_API(ctx, actor)
    location_name = CITY_SLOT(api_input)
    return weather_forecast_now(location_name)


def news_api_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    query_params = {"source": "bbc-news", "sortBy": "top", "apiKey": available_variables["NEWS_API_KEY"]}
    main_url = " https://newsapi.org/v1/articles"
    res = requests.get(main_url, params=query_params)
    open_bbc_page = res.json()
    article = open_bbc_page["articles"]
    results = []
    for ar in article:
        results.append(ar["title"])

    return "\n".join(results)


def wolframalpha_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    try:
        api_input = compose_input_for_API(ctx, actor)
        client = wolframalpha.Client(available_variables["WOLFRAMALPHA_APP_ID"])
        res = client.query(api_input)
        answer = next(res.results).text
    except StopIteration:
        answer = "Unfortunately, something went wrong and I couldn't handle \
your request using WolframAlpha API."
    return answer


api_func_mapping = {
    "google_api": google_api_response,
    "generative_lm": generative_response,
    "weather_api": weather_api_response,
    "news_api": news_api_response,
    "wolframalpha_api": wolframalpha_response,
}


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
                            response = api_func_mapping[api2use](ctx, actor)
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
                                    response = api_func_mapping[api2use](ctx, actor)
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
                response = api_func_mapping[api2use](ctx, actor)
        else:
            response = None

        try:
            return response
        except UnboundLocalError:
            api2use = "generative_lm"
            int_ctx.save_to_shared_memory(ctx, actor, api2use=api2use)
            response = api_func_mapping[api2use](ctx, actor)
            return response


def response_with_approved_api(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    if not ctx.validation:
        shared_memory = int_ctx.get_shared_memory(ctx, actor)
        api2use = shared_memory.get("api2use", None)
        timeout = api_conf[api2use]["timeout"]
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
        try:
            response = api_func_mapping[api2use](ctx, actor)
        except Exception:
            response = "Unfortunately, somthing went wrong with API"
        signal.alarm(0)
        return response
