import logging
import sentry_sdk
from os import getenv

from df_engine.core import Context, Actor

from langchain.agents import Tool
from langchain.memory import ConversationBufferMemory
from langchain import OpenAI
from langchain.utilities import GoogleSearchAPIWrapper
from langchain.agents import initialize_agent


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

sending_variables = {f"{var}": getenv(var, None) for var in ["OPENAI_API_KEY", "GOOGLE_CSE_ID", "GOOGLE_API_KEY"]}
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
