import logging
import common.dff.integration.processing as int_prs
import common.dff.integration.context as int_ctx
from df_engine.core import Actor, Context


logger = logging.getLogger(__name__)
# ....

def save_previous_utterance(slot_name):

    def previous_human_utterance(
        ctx: Context,
        actor: Actor,
        *args,
        **kwargs,
    ) -> Context:
        human_text = int_ctx.get_last_human_utterance(ctx, actor)["text"]
        ctx = int_prs.save_slots_to_ctx({slot_name: human_text})(ctx, actor)
        return ctx

    return previous_human_utterance