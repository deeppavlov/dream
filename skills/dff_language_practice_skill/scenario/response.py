import logging
import json
import random
import os
import requests
from os import getenv

from df_engine.core import Context, Actor
import common.dff.integration.context as int_ctx
from common.acknowledgements import GENERAL_ACKNOWLEDGEMENTS

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

acknowledgements = GENERAL_ACKNOWLEDGEMENTS["EN"]["positive"] + GENERAL_ACKNOWLEDGEMENTS["EN"]["neutral"]


def example_response(reply: str):
    def example_response_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        return reply

    return example_response_handler


def intro_response():
    def intro_response_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        if not ctx.validation:
            dialog_script_name = None
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
            description = dialog["situation_description"]
            ctx.misc["agent"]["response"].update({"situation_description": description})
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
            processed_node = ctx.last_request
            shared_memory = int_ctx.get_shared_memory(ctx, actor)
            dialog_script_name = shared_memory.get("dialog_script_name", None)
            if dialog_script_name == None:
                return "We can role play some discussions on different topics."

            dialog_step_id = shared_memory.get("dialog_step_id", 0)
            dialog = scenarios[dialog_script_name]
            used_nodes_ids = shared_memory.get("used_nodes_ids", {})

            if dialog_script_name not in used_nodes_ids.keys():
                used_nodes_ids[dialog_script_name] = []

            if "repeat" in processed_node.lower():
                int_ctx.save_to_shared_memory(ctx, actor, dialog_step_id=dialog_step_id)
                int_ctx.save_to_shared_memory(ctx, actor, dialog_script_name=dialog_script_name)
                instructions = dialog["utterances"][1:-1][dialog_step_id]["P"]
                ctx.misc["agent"]["response"].update({"user_instructions": instructions})
                return dialog["utterances"][1:-1][dialog_step_id]["Q"]

            for i, utt in bot_questions[dialog_script_name]:
                if i not in used_nodes_ids[dialog_script_name]:
                    used_nodes_ids[dialog_script_name].append(i)
                    int_ctx.save_to_shared_memory(ctx, actor, dialog_step_id=i)
                    int_ctx.save_to_shared_memory(ctx, actor, used_nodes_ids=used_nodes_ids)
                    int_ctx.save_to_shared_memory(ctx, actor, dialog_script_name=dialog_script_name)
                    instructions = dialog["utterances"][1:-1][i]["P"]
                    ctx.misc["agent"]["response"].update({"user_instructions": instructions})
                    return dialog["utterances"][1:-1][i]["Q"]

            int_ctx.save_to_shared_memory(ctx, actor, dialog_step_id=-1)
            int_ctx.save_to_shared_memory(ctx, actor, dialog_script_name=dialog_script_name)
            instructions = dialog["utterances"][-1]["info_for_user"]
            ctx.misc["agent"]["response"].update({"user_instructions": instructions})
            return dialog["utterances"][-1]["utterance"]

    return follow_scenario_response_handler


def acknowledgement_response():
    def acknowledgement_response_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        if not ctx.validation:
            return random.choice(acknowledgements)

    return acknowledgement_response_handler


def repeat_response():
    def repeat_response_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        if not ctx.validation:
            return ctx.misc["agent"]["dialog"]["bot_utterances"][-1]["text"]

    return repeat_response_handler


def previous_response():
    def previous_response_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        if not ctx.validation:
            human_utterances = ctx.misc["agent"]["dialog"]["human_utterances"][-1]["user"]
            state = human_utterances["attributes"]["dff_language_practice_skill_state"]
            responses = state["context"]["responses"]
            prev_index = list(responses.keys())[-2]
            reply = responses[prev_index]
            return reply

    return previous_response_handler
