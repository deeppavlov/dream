import logging
import common.dff.integration.context as int_ctx

from df_engine.core import Context, Actor


logger = logging.getLogger(__name__)


def chapters(ctx: Context, actor: Actor, excluded_skills=None, *args, **kwargs) -> str:
    chapters = (
        int_ctx.get_last_human_utterance(ctx, actor)
        .get("annotations", {})
        .get("vidchapter_service", {})
        .get("video_captioning", "Error") # normally video_captioning is a dict 
    )

    error_response = "I couldn't caption the video in your message, please try again with another file"
    success_response = f"There are {chapters} in that video"

    rsp = error_response if chapters == "Error" else success_response

    return rsp
