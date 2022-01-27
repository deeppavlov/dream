import logging
import os
import requests

from dff.core import Context, Actor
import common.dff.integration.context as int_ctx
import common.constants as common_constants

logger = logging.getLogger(__name__)
# ....
CONF_HIGH = 1.0
CONF_MIDDLE = 0.95
CONF_LOW = 0.9
CONF_SUPER_LOW = 0.1


def example_response(reply: str):
    def example_response_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        return reply

    return example_response_handler


def error_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    logger.info(ctx, actor)
    int_ctx.set_confidence(ctx, actor, CONF_SUPER_LOW)
    return "Sorry"


def ontology_info_response(ctx: Context, actor: Actor) -> str:
    try:
        reply = ""
        # Temporary case-sensitive
        # utt = state_utils.get_last_human_utterance(vars)["text"].lower()
        utt = int_ctx.get_last_human_utterance(ctx, actor).get("text", "")
        logger.error(f"ontology_utt {utt}")
        # TODO: Search node in Ontology

        response = requests.post(os.environ["GRAPH_DB_URL"] + "/trigger", json={"sentence": utt})
        js = response.json()
        if "topic" in js.keys() and "answer" in js.keys():
            topic = js["topic"]
            reply = js["answer"]

            # response = "Yes, it is my favourite actor!"
            # state_utils.set_confidence(vars, confidence=CONF_HIGH)
            # state_utils.set_can_continue(vars, continue_flag=CAN_NOT_CONTINUE)
            int_ctx.set_confidence(ctx, actor, confidence=CONF_HIGH)
            int_ctx.set_can_continue(ctx, actor, continue_flag=common_constants.CAN_NOT_CONTINUE)

            # shared_memory = state_utils.get_shared_memory(vars)
            shared_memory = int_ctx.get_shared_memory(ctx, actor)
            used_topics = shared_memory.get("used_topics", [])
            # state_utils.save_to_shared_memory(vars, used_topics=used_topics + [topic])
            int_ctx.save_to_shared_memory(ctx, actor, used_topics=used_topics + [topic])

        return reply
    except Exception as exc:
        logger.info("WTF in ontology_info_response")
        logger.exception(exc)
        int_ctx.set_confidence(ctx, actor, 0)

        return "Sorry"


def ontology_detailed_info_response(ctx: Context, actor: Actor) -> str:
    try:
        reply = ""
        # Temporary case-sensitive
        # utt = state_utils.get_last_human_utterance(vars)["text"].lower()
        utt = int_ctx.get_last_human_utterance(ctx, actor).get("text", "")
        logger.error(f"ontology_utt {utt}")
        # TODO: Search node in Ontology

        # state_utils.set_confidence(vars, confidence=CONF_HIGH)
        # state_utils.set_can_continue(vars, continue_flag=CAN_NOT_CONTINUE)
        int_ctx.set_confidence(ctx, actor, confidence=CONF_HIGH)
        int_ctx.set_can_continue(ctx, actor, continue_flag=common_constants.CAN_NOT_CONTINUE)

        # shared_memory = state_utils.get_shared_memory(vars)
        shared_memory = int_ctx.get_shared_memory(ctx, actor)
        used_topics = shared_memory.get("used_topics", [])
        if len(used_topics) != 0:
            topic = used_topics[-1].replace('_', ' ')
            response = requests.post(os.environ["GRAPH_DB_URL"] + "/detailed_trigger", json={"sentence": topic})
            js = response.json()
            if "answer" in js.keys():
                reply = js["answer"]

        return reply
    except Exception as exc:
        logger.info("WTF in ontology_detailed_info_response")
        logger.exception(exc)
        int_ctx.set_confidence(ctx, actor, 0)

        return "Sorry"
