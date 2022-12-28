import logging
import re

from df_engine.core import Context, Actor
import common.dff.integration.context as int_ctx

from common.utils import yes_templates


logging.basicConfig(format="%(asctime)s - %(pathname)s - %(lineno)d - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)


def show_feedback4cancelled_dialog():
    def show_feedback4cancelled_dialog_handler(ctx: Context, actor: Actor, *args, **kwargs):
        processed_node = ctx.last_request
        logger.info(f"processed_node = {processed_node}")
        if re.search(yes_templates, processed_node.lower()):
            int_ctx.save_to_shared_memory(ctx, actor, show_feedback4cancelled_dialog=True)

    return show_feedback4cancelled_dialog_handler
