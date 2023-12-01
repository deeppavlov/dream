import logging
import common.dff.integration.context as int_ctx

from df_engine.core import Context, Actor


logger = logging.getLogger(__name__)


def caption(ctx: Context, actor: Actor, excluded_skills=None, *args, **kwargs) -> str:
    cap = (
        int_ctx.get_last_human_utterance(ctx, actor)
        .get("annotations", {})
        .get("voice_service", {})
        .get("caption", "Error")
    )

    error_response = "I couldn't caption the audio in your message, please try again with another file"
    success_response = f"Is there {cap} in that audio?"

    rsp = error_response if cap == "Error" else success_response

    return rsp
