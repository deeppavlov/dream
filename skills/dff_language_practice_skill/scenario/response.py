import logging
import json
import random

from df_engine.core import Context, Actor
import common.dff.integration.context as int_ctx


logger = logging.getLogger(__name__)
# ....


def example_response(reply: str):
    def example_response_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        return reply

    return example_response_handler


def response_from_data():
    def response_from_data_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        shared_memory = int_ctx.get_shared_memory(ctx, actor)
        dialog_step_id = shared_memory.get("dialog_step_id", 0)
        dialog_script_name = shared_memory.get("dialog_script_name", None)
        if dialog_script_name is None:
            dialog_script_name = random.choice(["luggage", "job_interview"])

        f = open(f'data/{dialog_script_name}.json')
        dialog = json.load(f)
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
