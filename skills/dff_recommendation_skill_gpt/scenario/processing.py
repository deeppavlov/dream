import logging
import common.dff.integration.processing as int_prs
import common.dff.integration.context as int_ctx
from df_engine.core import Actor, Context
import requests
from os import getenv
# ....

logger = logging.getLogger(__name__)
# ....


def save_previous_utterance_nps(slot_name):

    def previous_human_utterance_nps(
        ctx: Context,
        actor: Actor,
        *args,
        **kwargs,
    ) -> Context:
        human_text = int_ctx.get_nounphrases_from_human_utterance(ctx, actor)
        if human_text:
            ctx = int_prs.save_slots_to_ctx({slot_name: ' '.join(human_text)})(ctx, actor)
        return ctx

    return previous_human_utterance_nps


def save_user_name(slot_name):

    def get_name(
        ctx: Context,
        actor: Actor,
        *args,
        **kwargs,
    ) -> Context:
        human_text = str(int_ctx.get_nounphrases_from_human_utterance(ctx, actor))
        ctx = int_prs.save_slots_to_ctx({slot_name: human_text})(ctx, actor)
        return ctx

    return get_name

