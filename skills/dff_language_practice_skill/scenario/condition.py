import logging
import os
import json

from df_engine.core import Context, Actor

from common.dff.integration import condition as int_cnd
import common.dff.integration.context as int_ctx

logger = logging.getLogger(__name__)
# ....


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
                    dialog_step_id += 1
                    int_ctx.save_to_shared_memory(ctx, actor, dialog_step_id=dialog_step_id)
                    int_ctx.save_to_shared_memory(ctx, actor, dialog_script_name=found_dialog_script_name)
                    logger.info(f"""dialog_script_name: {found_dialog_script_name}""")
                    return True

        return False

    return is_intro_handler
