import logging
import sentry_sdk
import json
import re
import requests
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

GENERATIVE_SERVICE_URL = getenv("GENERATIVE_SERVICE_URL", "http://openai-api-chatgpt:8145/respond")
GENERATIVE_SERVICE_CONFIG = getenv("GENERATIVE_SERVICE_CONFIG", "openai-chatgpt.json")
GENERATIVE_TIMEOUT = int(getenv("GENERATIVE_TIMEOUT", 5))
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
    last_uttr = int_ctx.get_last_human_utterance(ctx, actor)
    prompt = last_uttr.get("attributes", {}).get("prompt", "Respond like a friendly chatbot.")
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
    location_name = CITY_SLOT(ctx.last_request)
    return weather_forecast_now(location_name)


api_func_mapping = {
    "google_api": google_api_response,
    "generative_lm": generative_response,
    "weather_api": weather_api_response,
}


def response_with_chosen_api(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    if not ctx.validation:
        prompt = f"""You have a dictionary of tools where keys are the names \
of the tools and values are dictionaries with tool descriptions:
{top_n_apis}
Based on these descriptions, choose the best tool to use in order to answer \
the following user request: {ctx.last_request}
Return the name of the best tool exactly as it is written in the dictionary. \
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
            response = api_func_mapping[hypotheses[0]](ctx, actor)
        except KeyError:
            response = api_func_mapping["generative_lm"](ctx, actor)
        return response
