import logging

from df_engine.core import Context, Actor

from common.dff.integration import condition as int_cnd
import common.dff.integration.context as int_ctx

logging.basicConfig(format="%(asctime)s - %(pathname)s - %(lineno)d - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)


def example_lets_talk_about():
    def example_lets_talk_about_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        return int_cnd.is_lets_chat_about_topic_human_initiative(ctx, actor)

    return example_lets_talk_about_handler


def is_end_dialog():
    def is_end_dialog_handler(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
        agent = ctx.misc.get("agent", {})
        dialog = ctx.misc.get("agent", {}).get("dialog", {}).get("human_utterances", [{}])[-1]
        last_utterance = dialog.get("user", {})
        practice_skill_state = last_utterance.get("attributes", {}).get("dff_language_practice_skill_state", {})
        scenario_len = practice_skill_state.get("shared_memory", {}).get("scenario_len", 0)
        dialog_step_id = practice_skill_state.get("shared_memory", {}).get("dialog_step_id", 0)
        if ((scenario_len - 1) == dialog_step_id) and (dialog_step_id != 0):
            return True

        feedback4cancelled_dialog = practice_skill_state.get("shared_memory", {}).get(
            "show_feedback4cancelled_dialog", False
        )
        if feedback4cancelled_dialog:
            return True

        return False

    return is_end_dialog_handler
