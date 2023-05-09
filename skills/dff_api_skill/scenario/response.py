import logging
import sentry_sdk
import json
import re
import requests
import random
from os import getenv
from typing import Any

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

GENERATIVE_TIMEOUT = int(getenv("GENERATIVE_TIMEOUT", 5))
N_UTTERANCES_CONTEXT = int(getenv("N_UTTERANCES_CONTEXT", 3))

FIX_PUNCTUATION = re.compile(r"\s(?=[\.,:;])")
DEFAULT_CONFIDENCE = 0.9
LOW_CONFIDENCE = 0.7

CONSIDERED_LM_SERVICES = {
    "GPT-J 6B": {
        "url": "http://transformers-lm-gptj:8130/respond",
        "config": json.load(open("generative_configs/default_generative_config.json", "r")),
    },
    "BLOOMZ 7B": {
        "url": "http://transformers-lm-bloomz7b:8146/respond",
        "config": json.load(open("generative_configs/default_generative_config.json", "r")),
    },
    "ChatGPT": {
        "url": "http://openai-api-chatgpt:8145/respond",
        "config": json.load(open("generative_configs/openai-chatgpt.json", "r")),
        "envvars_to_send": ["OPENAI_API_KEY", "OPENAI_ORGANIZATION"],
    },
    "GPT-3.5": {
        "url": "http://openai-api-davinci3:8131/respond",
        "config": json.load(open("generative_configs/openai-text-davinci-003.json", "r")),
        "envvars_to_send": ["OPENAI_API_KEY", "OPENAI_ORGANIZATION"],
    },
}

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
        answer = agent_chain.run(ctx.last_request)
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
    logger.info(f"dialog_context: {dialog_context}")
    last_uttr = int_ctx.get_last_human_utterance(ctx, actor)
    prompt = last_uttr.get("attributes", {}).get("prompt", "Respond like a friendly chatbot.")
    logger.info(f"prompt: {prompt}")
    lm_service = last_uttr.get("attributes", {}).get("lm_service", "GPT-J 6B")
    logger.info(f"lm_service: {lm_service}")

    if "envvars_to_send" in CONSIDERED_LM_SERVICES[lm_service]:
        sending_variables = {
            f"{var}_list": [getenv(var, None)] for var in CONSIDERED_LM_SERVICES[lm_service]["envvars_to_send"]
        }
        # check if at least one of the env variables is not None
        if len(sending_variables.keys()) > 0 and all([var_value is None for var_value in sending_variables.values()]):
            raise NotImplementedError(
                "ERROR: All environmental variables have None values. At least one of them must have not None value"
            )
    else:
        sending_variables = {}

    if len(dialog_context) > 0:
        response = requests.post(
            CONSIDERED_LM_SERVICES[lm_service]["url"],
            json={
                "dialog_contexts": [dialog_context],
                "prompts": [prompt],
                "configs": [CONSIDERED_LM_SERVICES[lm_service]["config"]],
                **sending_variables,
            },
            timeout=GENERATIVE_TIMEOUT,
        )
        hypotheses = response.json()[0]
    else:
        hypotheses = []
    logger.info(f"generated hypotheses: {hypotheses}")
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
    location_name = CITY_SLOT(ctx.last_request)
    return weather_forecast_now(location_name)


api_func_mapping = {
    "google_api": google_api_response,
    "transformers_lm": generative_response,
    "weather_api": weather_api_response
}

def response_with_chosen_api(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    if not ctx.validation:
        api_to_use = choose_api(top_n_apis)
        response = api_func_mapping[api_to_use]
        return response


def choose_api(top_n_apis): 
    # we will add some function to retrieve top_n_apis from a database, 
    # now we imagine that we already have it
    prompt = f"""You have a dictionary of tools where keys are the names of the tools and values are dictionaries with tool descriptions:
    {top_n_apis}
    Based on these descriptions, choose the best tool to use in order to answer the following user request:
    {ctx.last_request}
    Return the name of the best tool exactly as it is written in the dictionary."""
    best_api = requests.post(
            CONSIDERED_LM_SERVICES[lm_service]["url"],
            json={
                "dialog_contexts": [dialog_context],
                "prompts": [prompt],
                "configs": [CONSIDERED_LM_SERVICES[lm_service]["config"]],
                **sending_variables,
            },
            timeout=GENERATIVE_TIMEOUT,
        )
    return best_api
    
    
    

