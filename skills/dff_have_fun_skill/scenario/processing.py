import logging
import re
import json

from df_engine.core import Node, Context, Actor

logger = logging.getLogger(__name__)
# ....

with open('common/QA_jokes.json', 'r') as f:
    jokes = json.load(f)


def extract_jokes():
    def save_slots_to_ctx_processing(
        ctx: Context,
        actor: Actor,
        *args,
        **kwargs,
    ) -> Context:
        slots = ctx.misc.get("slots", {})
        for i, joke in enumerate(jokes['qa_jokes']):
            slots['Q' + str(i)] = joke[0]
            slots['A' + str(i)] = joke[1]

        ctx.misc["slots"] = slots
        return ctx

    return save_slots_to_ctx_processing