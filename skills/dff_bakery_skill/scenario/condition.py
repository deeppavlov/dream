import logging

from df_engine.core import Context, Actor

from common.dff.integration import condition as int_cnd

from flask import request

logger = logging.getLogger(__name__)
# ....


def example_lets_talk_about():
    def example_lets_talk_about_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        return int_cnd.is_lets_chat_about_topic_human_initiative(ctx, actor)

    return example_lets_talk_about_handler

def do_something():
    uttrs = request.json.get("utterances", [])
    utt = uttrs[0]
    annotations = uttrs[0].get("annotations", {})
    custom_el_annotations = annotations.get("custom_entity_linking", [])
    logger.info(f"utt --- {utt}")
    logger.info(f"custom_el_annotations --- {custom_el_annotations}")

# do_something()