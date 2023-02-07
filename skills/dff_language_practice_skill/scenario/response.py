import logging
import json
import random
import os
import requests
from os import getenv

from df_engine.core import Context, Actor
import common.dff.integration.context as int_ctx

SENTENCE_RANKER_SERVICE_URL = getenv("SENTENCE_RANKER_SERVICE_URL")

logging.basicConfig(format="%(asctime)s - %(pathname)s - %(lineno)d - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)

scenarios = {}
for filename in os.listdir("data"):
    f = os.path.join("data", filename)
    if os.path.isfile(f):
        dialog = json.load(open(f))
        scenarios[filename.replace(".json", "")] = dialog

user_questions = {}
bot_questions = {}
for filename in os.listdir("data"):
    f = os.path.join("data", filename)
    if os.path.isfile(f):
        dialog = json.load(open(f))
        utts = dialog["utterances"][1:-1]
        questions = [(i, x["P"]) for i, x in enumerate(utts) if "ask" in x["P"].lower()]
        user_questions[filename.replace(".json", "")] = questions
        not_user_questions = [(i, x["Q"]) for i, x in enumerate(utts) if x["Q"] != ""]
        bot_questions[filename.replace(".json", "")] = not_user_questions

used_nodes_ids = {}


def example_response(reply: str):
    def example_response_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        return reply

    return example_response_handler


def intro_response():
    def intro_response_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        if not ctx.validation:
            processed_node = ctx.last_request
            for name, dialog in scenarios.items():
                keywords = dialog["keywords"]
                for keyword in keywords:
                    if keyword in processed_node.lower():
                        dialog_script_name = name
                        continue

            dialog = scenarios[dialog_script_name]
            reply = dialog["utterances"][0]["utterance"]
            int_ctx.save_to_shared_memory(ctx, actor, dialog_script_name=dialog_script_name)
            return reply

    return intro_response_handler


def answer_known_question():
    def answer_known_question_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        if not ctx.validation:
            processed_node = ctx.last_request
            shared_memory = int_ctx.get_shared_memory(ctx, actor)
            dialog_script_name = shared_memory.get("dialog_script_name", None)
            sentence_pairs = [[x[1], processed_node] for x in user_questions[dialog_script_name]]
            request_data = {"sentence_pairs": sentence_pairs}
            result = requests.post(SENTENCE_RANKER_SERVICE_URL, json=request_data).json()[0]["batch"]
            max_conf = max(result)
            index_max_conf = result.index(max_conf)
            answer_index = user_questions[dialog_script_name][index_max_conf][0]
            dialog = scenarios[dialog_script_name]
            reply = dialog["utterances"][1:-1][answer_index]["A"]
            return reply

    return answer_known_question_handler


def follow_scenario_response():
    def follow_scenario_response_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        if not ctx.validation:
            shared_memory = int_ctx.get_shared_memory(ctx, actor)
            dialog_script_name = shared_memory.get("dialog_script_name", None)
            dialog = scenarios[dialog_script_name]
            if dialog_script_name not in used_nodes_ids.keys():
                used_nodes_ids[dialog_script_name] = []

            for i, utt in bot_questions[dialog_script_name]:
                if i not in used_nodes_ids[dialog_script_name]:
                    used_nodes_ids[dialog_script_name].append(i)
                    int_ctx.save_to_shared_memory(ctx, actor, dialog_step_id=i)
                    return dialog["utterances"][1:-1][i]["Q"]

            int_ctx.save_to_shared_memory(ctx, actor, dialog_step_id=-1)
            return dialog["utterances"][-1]["utterance"]

    return follow_scenario_response_handler
