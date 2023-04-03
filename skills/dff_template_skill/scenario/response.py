import logging

from dff.script import Context


logger = logging.getLogger(__name__)
# ....


def example_response(reply: str):
    def example_response_handler(ctx: Context, _) -> str:
        return reply

    return example_response_handler
