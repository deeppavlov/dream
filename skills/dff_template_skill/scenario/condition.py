import logging

from dff.script import Context
from dff.pipeline import Pipeline

from common.dff_api_v1.integration import condition as int_cnd

logger = logging.getLogger(__name__)
# ....


def example_lets_talk_about():
    def example_lets_talk_about_handler(ctx: Context, pipeline: Pipeline) -> str:
        return int_cnd.is_lets_chat_about_topic_human_initiative(ctx, pipeline)

    return example_lets_talk_about_handler
