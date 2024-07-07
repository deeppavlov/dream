import logging

from df_engine.core import Context, Actor
import common.dff.integration.context as int_ctx

logger = logging.getLogger(__name__)


def video_detected(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    video_captioning = int_ctx.get_last_human_utterance(ctx, actor).get("annotations", {}).get("vidchapters_service", {})
    logger.info(f"CONDITION.PY VIDCHAPTERS: {video_captioning}")
    if video_captioning.get("video_captioning_chapters", "Error") != "Error":
        return True
    return False
