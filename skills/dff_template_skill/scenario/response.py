import logging

from df_engine.core import Context, Actor


logger = logging.getLogger(__name__)
# ....


def example_response(reply: str):
    def example_response_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        return reply

    return example_response_handler
