import logging
import re

from df_engine.core import Context, Actor
from scenario.response_funcs import get_response_funcs
from common.dff.integration import condition as int_cnd
import common.utils as common_utils
import common.dff.integration.context as int_ctx

logger = logging.getLogger(__name__)
# ....


# def example_lets_talk_about():
#     def example_lets_talk_about_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
#         return int_cnd.is_lets_chat_about_topic_human_initiative(ctx, actor)

#     return example_lets_talk_about_handler


def is_intent(target_intent_name="look_at_user"):
    def is_known_intent_handler(ctx: Context, actor: Actor, *args, **kwargs):
        if ctx.validation:
            return False
        
        detected_intents = common_utils.get_intents(
            int_ctx.get_last_human_utterance(ctx, actor),
            probs=False,
            which="minecraft_bot",
        )

        logger.debug(f"Checking for detected intents: {str(detected_intents)}")

        if len(detected_intents)==0:
            return False
        
        detected_intent = detected_intents[0]

        if detected_intent == target_intent_name:
            return True
        return False
    
    return is_known_intent_handler


# def minecraft_intent_exists_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
#     if ctx.validation:
#         return False

#     intents_by_minecraft_bot = common_utils.get_intents(
#         int_ctx.get_last_human_utterance(ctx, actor),
#         probs=False,
#         which="minecraft_bot",
#     )

#     response_funcs = get_response_funcs()
#     return bool(any([intent in response_funcs for intent in intents_by_minecraft_bot]))

def is_known_object():
    def is_known_object_handler(ctx: Context, actor: Actor, *args, **kwargs):
        known_objects = list(ctx.misc.get("slots", {}).values())
        if known_objects:
            objects_re = "|".join(known_objects)
            return bool(re.findall(objects_re, ctx.last_request, re.IGNORECASE))

        return False
    
    return is_known_object_handler