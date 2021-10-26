import random
from .core.context import Context
from .core.actor import Actor


def choice(responses: list):
    def choice_response_handler(ctx: Context, actor: Actor, *args, **kwargs):
        return random.choice(responses)

    return choice_response_handler
