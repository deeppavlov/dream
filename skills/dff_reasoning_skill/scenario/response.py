import logging
import sentry_sdk
import json
import re
import requests
from os import getenv
from typing import Any
import time
import wolframalpha
import arxiv

from langchain.agents import Tool
from langchain.memory import ConversationBufferMemory
from langchain import OpenAI
from langchain.utilities import GoogleSearchAPIWrapper
from langchain.agents import initialize_agent

from df_engine.core import Context, Actor
import common.dff.integration.context as int_ctx
import common.dff.integration.response as int_rsp
from common.constants import CAN_NOT_CONTINUE

from tools.city_slot import OWMCitySlot
from tools.weather_service import weather_forecast_now

with open("api_conf.json", "r") as f:
    top_n_apis = json.load(f)

CITY_SLOT = OWMCitySlot()


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

GENERATIVE_SERVICE_URL = getenv("GENERATIVE_SERVICE_URL", "http://openai-api-chatgpt:8145/respond")
GENERATIVE_SERVICE_CONFIG = getenv("GENERATIVE_SERVICE_CONFIG", "openai-chatgpt.json")
GENERATIVE_TIMEOUT = int(getenv("GENERATIVE_TIMEOUT", 30))
N_UTTERANCES_CONTEXT = int(getenv("N_UTTERANCES_CONTEXT", 1))

FIX_PUNCTUATION = re.compile(r"\s(?=[\.,:;])")
DEFAULT_CONFIDENCE = 0.9
LOW_CONFIDENCE = 0.7

ENVVARS_TO_SEND = getenv("ENVVARS_TO_SEND", None)
ENVVARS_TO_SEND = [] if ENVVARS_TO_SEND is None else ENVVARS_TO_SEND.split(",")
sending_variables = {f"{var}": getenv(var, None) for var in ENVVARS_TO_SEND}
# check if at least one of the env variables is not None
if len(sending_variables.keys()) > 0 and all([var_value is None for var_value in sending_variables.values()]):
    raise NotImplementedError(
        "ERROR: All environmental variables have None values. At least one of the variables must have not None value"
    )

assert sending_variables["OPENAI_API_KEY"], logger.info("Type in OpenAI API key to `.env_scret`")
assert sending_variables["GOOGLE_CSE_ID"], logger.info("Type in GOOGLE CSE ID to `.env_scret`")
assert sending_variables["GOOGLE_API_KEY"], logger.info("Type in GOOGLE API key to `.env_scret`")
assert sending_variables["NEWS_API_KEY"], logger.info("Type in NEWS API key to `.env_scret`")
assert sending_variables["WOLFRAMALPHA_APP_ID"], logger.info("Type in WOLFRAMALPHA APPID key to `.env_scret`")

search = GoogleSearchAPIWrapper()
tools = [
    Tool(
        name="Current Search",
        func=search.run,
        description="useful when you need to answer questions about current events or the current state of the world",
    ),
]
memory = ConversationBufferMemory(memory_key="chat_history")
llm = OpenAI(temperature=0)
agent_chain = initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=True, memory=memory)


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
    prompt = compose_input_for_API(ctx, actor)
    if len(dialog_context) > 0:
        response = requests.post(
            GENERATIVE_SERVICE_URL,
            json={
                "dialog_contexts": [dialog_context],
                "prompts": [prompt],
                "configs": [json.load(open(f"common/generative_configs/{GENERATIVE_SERVICE_CONFIG}", "r"))],
                "openai_api_keys": [sending_variables["OPENAI_API_KEY"]],
            },
            timeout=GENERATIVE_TIMEOUT,
        )
        hypotheses = response.json()[0]
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
    query_params = {"source": "bbc-news", "sortBy": "top", "apiKey": sending_variables["NEWS_API_KEY"]}
    main_url = " https://newsapi.org/v1/articles"
    res = requests.get(main_url, params=query_params)
    open_bbc_page = res.json()
    article = open_bbc_page["articles"]
    results = []
    for ar in article:
        results.append(ar["title"])

    return "\n".join(results)


def wolframalpha_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    api_input = compose_input_for_API(ctx, actor)
    client = wolframalpha.Client(sending_variables["WOLFRAMALPHA_APP_ID"])
    res = client.query(api_input)
    answer = next(res.results).text
    return answer


def arxiv_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    api_input = compose_input_for_API(ctx, actor)
    search = arxiv.Search(
        query = api_input,
        max_results = 3,
        sort_by = arxiv.SortCriterion.SubmittedDate
        )
    
    response = ""
    for result in search.results():
        response += f"TITLE: {result.title}.\nSUMMARY: {result.summary}\LINK: {result}\n\n"
    
    return response

api_func_mapping = {
    "google_api": google_api_response,
    "generative_lm": generative_response,
    "weather_api": weather_api_response,
    "news_api": news_api_response,
    "wolframalpha_api": wolframalpha_response,
    "arxiv_api": arxiv_response
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
        try:
            response = requests.post(
                GENERATIVE_SERVICE_URL,
                json={
                    "dialog_contexts": [dialog_context],
                    "prompts": [prompt],
                    "configs": [json.load(open(f"common/generative_configs/{GENERATIVE_SERVICE_CONFIG}", "r"))],
                    "openai_api_keys": [sending_variables["OPENAI_API_KEY"]],
                },
                timeout=GENERATIVE_TIMEOUT,
            )
            thought = response.json()[0][0]
        except KeyError:
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
        try:
            response = requests.post(
                GENERATIVE_SERVICE_URL,
                json={
                    "dialog_contexts": [dialog_context],
                    "prompts": [prompt],
                    "configs": [json.load(open(f"common/generative_configs/{GENERATIVE_SERVICE_CONFIG}", "r"))],
                    "openai_api_keys": [sending_variables["OPENAI_API_KEY"]],
                },
                timeout=GENERATIVE_TIMEOUT,
            )
            answer = response.json()[0][0]
        except KeyError:
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
        try:
            response = requests.post(
                GENERATIVE_SERVICE_URL,
                json={
                    "dialog_contexts": [dialog_context],
                    "prompts": [prompt],
                    "configs": [json.load(open(f"common/generative_configs/{GENERATIVE_SERVICE_CONFIG}", "r"))],
                    "openai_api_keys": [sending_variables["OPENAI_API_KEY"]],
                },
                timeout=GENERATIVE_TIMEOUT,
            )
            question = response.json()[0][0]
        except KeyError:
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
        input_template = top_n_apis[api2use]["input_template"]
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

        try:
            response = requests.post(
                GENERATIVE_SERVICE_URL,
                json={
                    "dialog_contexts": [dialog_context],
                    "prompts": [prompt],
                    "configs": [json.load(open(f"common/generative_configs/{GENERATIVE_SERVICE_CONFIG}", "r"))],
                    "openai_api_keys": [sending_variables["OPENAI_API_KEY"]],
                },
                timeout=GENERATIVE_TIMEOUT,
            )
            api_input = response.json()[0][0]
        except KeyError:
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
        prompt = f"""YOUR GOAL:
{thought}
AVAILABLE TOOLS:
{top_n_apis}
Choose the best tool to use to complete your task. \
Return the name of the best tool to use exactly as it is written in the dictionary. \
DON'T EXPLAIN YOUR DECISION, JUST RETURN THE KEY. E.x. google_api"""
        dialog_context = compose_data_for_model(ctx, actor)
        try:
            best_api = requests.post(
                GENERATIVE_SERVICE_URL,
                json={
                    "dialog_contexts": [dialog_context],
                    "prompts": [prompt],
                    "configs": [json.load(open(f"common/generative_configs/{GENERATIVE_SERVICE_CONFIG}", "r"))],
                    "openai_api_keys": [sending_variables["OPENAI_API_KEY"]],
                },
                timeout=GENERATIVE_TIMEOUT,
            )
            hypotheses = best_api.json()[0]
            try:
                if top_n_apis[hypotheses[0]]["needs_approval"] == "False":
                    api2use = hypotheses[0]
                    int_ctx.save_to_shared_memory(ctx, actor, api2use=api2use)
                    response = api_func_mapping[api2use](ctx, actor)
                else:
                    api2use = hypotheses[0]
                    int_ctx.save_to_shared_memory(ctx, actor, api2use=api2use)
                    response = f"""I need to use {api2use} to handle your request. Do you approve?"""
            except KeyError:
                for key in top_n_apis.keys():
                    if key in hypotheses[0]:
                        if top_n_apis[key]["needs_approval"] == "False":
                            api2use = key
                            int_ctx.save_to_shared_memory(ctx, actor, api2use=api2use)
                            response = api_func_mapping[api2use](ctx, actor)
                        else:
                            api2use = key
                            int_ctx.save_to_shared_memory(ctx, actor, api2use=api2use)
                            response = f"""I need to use {api2use} to handle your request. Do you approve?"""
                        break

        except KeyError:
            api2use = "generative_lm"
            int_ctx.save_to_shared_memory(ctx, actor, api2use=api2use)
            response = api_func_mapping[api2use](ctx, actor)

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
        response = api_func_mapping[api2use](ctx, actor)
        return response
