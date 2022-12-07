import logging
import json

from df_engine.core import Context, Actor

f = open('data/luggage.json')
dialog = json.load(f)
counter = 0

logger = logging.getLogger(__name__)
# ....


def example_response(reply: str):
    def example_response_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        return reply

    return example_response_handler


def response_from_data():
    def response_from_data_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        global counter
        if counter < len(dialog["utterances"]):
            reply = dialog["utterances"][counter]["utterance"]
            counter += 1
        
        else:
            counter = 0
            reply = dialog["utterances"][counter]["utterance"]
        
        return reply

    return response_from_data_handler
