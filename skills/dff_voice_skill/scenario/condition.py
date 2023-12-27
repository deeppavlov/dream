import logging

from df_engine.core import Context, Actor
import common.dff.integration.context as int_ctx

logger = logging.getLogger(__name__)


def voice_message_detected(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    voice = int_ctx.get_last_human_utterance(ctx, actor).get("annotations", {}).get("voice_service", {})
    logger.debug(f"CONDITION.PY VOICE: {voice}")
    if voice.get("caption", "Error") != "Error":
        return True
    return False
