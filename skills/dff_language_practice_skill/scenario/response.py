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
        shared_memory = int_ctx.get_shared_memory(ctx, actor)
        dialog_step_id = shared_memory.get("dialog_step_id", 0)
        dialog_script_name = shared_memory.get("dialog_script_name", None)
        processed_node = ctx.last_request
        if dialog_script_name is None:
            for filename in os.listdir("data"):
                f = os.path.join("data", filename)
                if os.path.isfile(f):
                    dialog = json.load(open(f))
                    keywords = dialog["keywords"]
                    for keyword in keywords:
                        if keyword in processed_node.lower():
                            logger.info(f"keyword: {keyword}")
                            logger.info(f"filename: {filename}")
                            dialog_script_name = filename.replace(".json", "")

                            if dialog_script_name is None:
                                return "We can role play some discussions on different topics."

                            if "repeat" in processed_node.lower():
                                reply = dialog["utterances"][dialog_step_id - 1]["utterance"]
                                int_ctx.save_to_shared_memory(ctx, actor, dialog_script_name=dialog_script_name)

                            elif "previous" in processed_node.lower():
                                reply = dialog["utterances"][dialog_step_id - 2]["utterance"]
                                dialog_step_id -= 1
                                int_ctx.save_to_shared_memory(ctx, actor, dialog_script_name=dialog_script_name)

                            else:
                                if dialog_step_id <= len(dialog["utterances"]):
                                    reply = dialog["utterances"][dialog_step_id]["utterance"]
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
