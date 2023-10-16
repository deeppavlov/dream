import logging

from df_engine.core import Context, Actor
import common.dff.integration.context as int_ctx

from common.dff.integration import condition as int_cnd

logger = logging.getLogger(__name__)

def voice_message_detected(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    voice = int_ctx.get_last_human_utterance(ctx, actor)\
        .get("annotations", {}).get("whisper_at_service", {})
    logger.debug(f"CONDITION.PY VOICE: {voice}")
    if voice is not None:
        return True
    return False



# def example_lets_talk_about():
#     def example_lets_talk_about_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
#         return int_cnd.is_lets_chat_about_topic_human_initiative(ctx, actor)

#     return example_lets_talk_about_handler
