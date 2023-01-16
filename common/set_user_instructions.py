import logging
import os
import random
import json

from df_engine.core import Context, Actor

logging.basicConfig(format="%(asctime)s - %(pathname)s - %(lineno)d - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)


def set_user_instructions():
    def set_user_instructions_handler(ctx: Context, actor: Actor):
        dialog_script_name = None
        if not ctx.validation:
            user_uttr = ctx.misc["agent"]["dialog"]["human_utterances"][-1]
            last_utterance = user_uttr.get("user", {})
            processed_node = ctx.last_request
            try:
                practice_skill_state = last_utterance.get("attributes", {}).get("dff_language_practice_skill_state", {})
                dialog_step_id = practice_skill_state["shared_memory"]["dialog_step_id"]
                dialog_step_id += 1
                dialog_script_name = practice_skill_state["shared_memory"]["dialog_script_name"]
            except:
                for filename in os.listdir("data"):
                    f = os.path.join("data", filename)
                    if os.path.isfile(f):
                        dialog = json.load(open(f))
                        keywords = dialog["keywords"]
                        for keyword in keywords:
                            if keyword in processed_node.lower():
                                dialog_script_name = filename.replace(".json", "")
                                dialog_step_id = 0
                                continue

            if dialog_script_name != None:
                f = f"data/{dialog_script_name}.json"
                scenario = json.load(open(f))
                instructions = scenario["utterances"][dialog_step_id]["info_for_user"]
                ctx.misc["agent"]["response"].update({"user_instructions": instructions})
        return ctx

    return set_user_instructions_handler


def set_situation_description():
    def set_situation_description_handler(ctx: Context, actor: Actor):
        dialog_script_name = None
        if not ctx.validation:
            user_uttr = ctx.misc["agent"]["dialog"]["human_utterances"][-1]
            last_utterance = user_uttr.get("user", {})
            processed_node = ctx.last_request
            for filename in os.listdir("data"):
                f = os.path.join("data", filename)
                if os.path.isfile(f):
                    dialog = json.load(open(f))
                    keywords = dialog["keywords"]
                    for keyword in keywords:
                        if keyword in processed_node.lower():
                            dialog_script_name = filename.replace(".json", "")
                            continue

            if dialog_script_name != None:
                f = f"data/{dialog_script_name}.json"
                scenario = json.load(open(f))
                description = scenario["situation_description"]
                ctx.misc["agent"]["response"].update({"situation_description": description})
        return ctx

    return set_situation_description_handler
