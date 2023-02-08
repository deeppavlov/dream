import logging
import os
import json
import requests
from os import getenv

from df_engine.core import Context, Actor

from common.dff.integration import condition as int_cnd
import common.dff.integration.context as int_ctx

SENTENCE_RANKER_SERVICE_URL = getenv("SENTENCE_RANKER_SERVICE_URL")

logger = logging.getLogger(__name__)
# ....

user_questions = {}
for filename in os.listdir("data"):
    f = os.path.join("data", filename)
    if os.path.isfile(f):
        dialog = json.load(open(f))
        utts = dialog["utterances"][1:-1]
        questions = [(i, x["P"]) for i, x in enumerate(utts) if "ask" in x["P"].lower()]
        user_questions[filename.replace(".json", "")] = questions


def example_lets_talk_about():
    def example_lets_talk_about_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        return int_cnd.is_lets_chat_about_topic_human_initiative(ctx, actor)

    return example_lets_talk_about_handler


def is_intro():
    def is_intro_handler(ctx: Context, actor: Actor, *args, **kwargs):
        if not ctx.validation:
            CERF_levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
            shared_memory = int_ctx.get_shared_memory(ctx, actor)
            dialog_step_id = shared_memory.get("dialog_step_id", -1)
            dialog_script_name = shared_memory.get("dialog_script_name", None)
            user_cerf = (
                ctx.misc.get("agent", {}).get("dialog", {}).get("human", {}).get("attributes", {}).get("CERF", "C2")
            )
            processed_node = ctx.last_request
            found_dialog_script_name = None
            for filename in os.listdir("data"):
                f = os.path.join("data", filename)
                if os.path.isfile(f):
                    dialog = json.load(open(f))
                    keywords = dialog["keywords"]
                    for keyword in keywords:
                        if keyword in processed_node.lower():
                            found_dialog_script_name = filename.replace(".json", "")
                            dialog_cerf = dialog["CEFR"]

                if (
                    (found_dialog_script_name != None)
                    and (dialog_script_name != found_dialog_script_name)
                    and (CERF_levels.index(user_cerf) >= CERF_levels.index(dialog_cerf))
                ):
                    return True

        return False

    return is_intro_handler


def is_known_question():
    def is_known_question_handler(ctx: Context, actor: Actor, *args, **kwargs):
        if not ctx.validation:
            processed_node = ctx.last_request
            shared_memory = int_ctx.get_shared_memory(ctx, actor)
            dialog_script_name = shared_memory.get("dialog_script_name", None)
            logger.info(f"""dialog_script_name: {dialog_script_name}""")
            if dialog_script_name != None:
                sentence_pairs = [[x[1], processed_node] for x in user_questions[dialog_script_name]]
                logger.info(f"""sentence_pairs: {sentence_pairs}""")
                request_data = {"sentence_pairs": sentence_pairs}
                result = requests.post(SENTENCE_RANKER_SERVICE_URL, json=request_data).json()[0]["batch"]
                logger.info(f"""result: {result}""")

                for conf in result:
                    if conf >= 0.7:
                        return True
        return False

    return is_known_question_handler


def is_acknowledgement():
    def is_acknowledgement_handler(ctx: Context, actor: Actor, *args, **kwargs):
        if not ctx.validation:
            human_utterances = ctx.misc["agent"]["dialog"]["human_utterances"][-1]["user"]
            state = human_utterances["attributes"]["dff_language_practice_skill_state"]
            responses = state["context"]["responses"]
            prev_index = list(responses.keys())[-2]
            prev_reply = responses[prev_index]
            if prev_reply != "We can role play some discussions on different topics.":
                return True

        return False

    return is_acknowledgement_handler
