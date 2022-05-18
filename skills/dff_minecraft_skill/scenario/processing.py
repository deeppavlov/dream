import logging
import re
import common.dff.integration.context as int_ctx
import common.dff.integration.processing as int_prs
from df_engine.core import Context, Actor


logger = logging.getLogger(__name__)

GO_TO_COMPILED_PATTERN = re.compile(r"(?:(?:go to)|(?:move to)|(?:come to)) (\d+)\,*\s*(\d+)\,*\s*(\d+)", re.IGNORECASE)

def get_destination():
    def get_destination_handler(ctx: Context, actor: Actor, *args, **kwargs):
        utt = int_ctx.get_last_human_utterance(ctx, actor)
        results = re.findall(GO_TO_COMPILED_PATTERN, utt)
        ctx = int_prs.save_slots_to_ctx({'dest1': 'science'})
        return ctx
    return get_destination_handler

def add_prefix(prefix):
    def add_prefix_processing(ctx: Context, actor: Actor, *args, **kwargs) -> Context:
        processed_node = ctx.framework_states["actor"].get("processed_node", ctx.framework_states["actor"]["next_node"])
        processed_node.response = f"{prefix}: {processed_node.response}"
        ctx.framework_states["actor"]["processed_node"] = processed_node
        return ctx

    return add_prefix_processing
