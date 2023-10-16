import logging

from df_engine.core import Context, Actor
import common.dff.integration.context as int_ctx


logger = logging.getLogger(__name__)

def caption(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    cap = "ERROR"
    if not ctx.validation:
        cap = int_ctx.get_last_human_utterance(ctx, actor).get("annotations", {}).get("whisper_at_service", {}).get("captions", "No captions")

    int_ctx.set_confidence(ctx, actor, 1)

    return f"{cap}"

def example_response(reply: str):
    def example_response_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        return reply

    return example_response_handler
