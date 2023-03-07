import logging

from df_engine.core import Context, Actor
import common.dff.integration.context as int_ctx

from common.dff.integration import condition as int_cnd

logger = logging.getLogger(__name__)


def voice_message_detected(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    voice = int_ctx.get_last_human_utterance(ctx, actor)\
        .get("annotations", {}).get("voice_service", {})
    logger.debug(f"CONDITION.PY VOICE: {voice}")
    if voice is not None:
        return True
    return False


def short_sound(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    duration = int_ctx.get_last_human_utterance(ctx, actor).get("annotations", {}).get("voice_service", {}).get("sound_duration")
    logger.debug(f'short_sound debug: {int_ctx.get_last_human_utterance(ctx, actor).get("annotations", {}).get("voice_service", {})}')
    if duration < 5:
        return True
    return False


def long_sound(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    duration = int_ctx.get_last_human_utterance(ctx, actor).get("annotations", {}).get("voice_service", {}).get("sound_duration")
    logger.debug(f'long_sound debug: {int_ctx.get_last_human_utterance(ctx, actor).get("annotations", {}).get("voice_service", {})}')
    if duration >= 5:
        return True
    return False