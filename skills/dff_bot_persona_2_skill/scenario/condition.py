import logging
import os
import requests

from df_engine.core import Context, Actor
import common.dff.integration.context as int_ctx

from common.dff.integration import condition as int_cnd

logger = logging.getLogger(__name__)
# ....


def example_lets_talk_about():
    def example_lets_talk_about_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        return int_cnd.is_lets_chat_about_topic_human_initiative(ctx, actor)

    return example_lets_talk_about_handler


def ontology_info_request(ctx: Context, actor: Actor) -> bool:
    # Temporary case-sensitive
    # utt = state_utils.get_last_human_utterance(vars)["text"].lower()
    utt = int_ctx.get_last_human_utterance(ctx, actor).get("text", "")

    logger.error(f"ontology_utt {utt}")

    response = requests.post(os.environ["GRAPH_DB_URL"] + "/can_trigger", json={"sentence": utt})

    logger.info(f"ontology response json {response.json()}")

    flag = response.json()

    logger.info(f"ontology_info_request {flag}")

    return flag


def ontology_detailed_info_request(ctx: Context, actor: Actor) -> bool:
    utt = int_ctx.get_last_human_utterance(ctx, actor).get("text", "")
    logger.error(f"ontology_utt {utt}")
    # TODO: More accurate intent matching (intent cather or regexp)

    # TODO: Search node in Ontology
    markers = ["tell me more", "else", "know more", "tell more", "something"]

    flag = False
    for marker in markers:
        flag |= utt.find(marker) != -1

    logger.info(f"ontology_detailed_info_request {flag}")

    return flag
