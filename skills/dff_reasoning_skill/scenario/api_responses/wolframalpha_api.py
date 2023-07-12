import wolframalpha
from os import getenv
from df_engine.core import Context, Actor
from scenario.utils import compose_input_for_API

ENVVARS_TO_SEND = getenv("ENVVARS_TO_SEND", None)
ENVVARS_TO_SEND = [] if ENVVARS_TO_SEND is None else ENVVARS_TO_SEND.split(",")
available_variables = {f"{var}": getenv(var, None) for var in ENVVARS_TO_SEND}


def wolframalpha_api_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    try:
        api_input = compose_input_for_API(ctx, actor)
        client = wolframalpha.Client(available_variables["WOLFRAMALPHA_APP_ID"])
        res = client.query(api_input)
        answer = next(res.results).text
    except StopIteration:
        answer = "Unfortunately, something went wrong and I couldn't handle \
your request using WolframAlpha API."
    return answer
