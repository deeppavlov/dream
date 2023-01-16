import logging
import json
import random
import os

from df_engine.core import Context, Actor
import common.dff.integration.context as int_ctx


logging.basicConfig(format="%(asctime)s - %(pathname)s - %(lineno)d - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)


def example_response(reply: str):
    def example_response_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        return reply

    return example_response_handler


def response_from_data():
    def response_from_data_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        CERF_levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
        shared_memory = int_ctx.get_shared_memory(ctx, actor)
        dialog_step_id = shared_memory.get("dialog_step_id", -1)
        dialog_script_name = shared_memory.get("dialog_script_name", None)
        user_cerf = ctx.misc.get("agent", {}).get("dialog", {}).get("human", {}).get("attributes", {}).get("CERF", "C2")
        processed_node = ctx.last_request
        found_dialog_script_name = None
        keywords_found = False
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
                keywords_found = True
                dialog_script_name = found_dialog_script_name
                dialog_step_id = -1
                break

        if (dialog_script_name != None) and (keywords_found == False):
            f = f"data/{dialog_script_name}.json"
            dialog = json.load(open(f))

        if dialog_script_name is None:
            return "We can role play some discussions on different topics."

        if "repeat" in processed_node.lower():
            reply = dialog["utterances"][dialog_step_id]["utterance"]
            int_ctx.save_to_shared_memory(ctx, actor, dialog_script_name=dialog_script_name)

        elif "previous" in processed_node.lower():
            reply = dialog["utterances"][dialog_step_id - 1]["utterance"]
            dialog_step_id -= 1
            int_ctx.save_to_shared_memory(ctx, actor, dialog_script_name=dialog_script_name)

        else:
            if dialog_step_id < (len(dialog["utterances"]) - 1):
                reply = dialog["utterances"][dialog_step_id + 1]["utterance"]
                dialog_step_id += 1
                int_ctx.save_to_shared_memory(ctx, actor, dialog_script_name=dialog_script_name)

            else:
                dialog_step_id = 0
                reply = dialog["utterances"][dialog_step_id]["utterance"]
                int_ctx.save_to_shared_memory(ctx, actor, dialog_script_name=dialog_script_name)

        int_ctx.save_to_shared_memory(ctx, actor, dialog_step_id=dialog_step_id)
        int_ctx.save_to_shared_memory(ctx, actor, scenario_len=len(dialog["utterances"]))

        return reply

    return response_from_data_handler
