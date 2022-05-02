import logging
import re
import json

from df_engine.core import Node, Context, Actor

logger = logging.getLogger(__name__)
# ....

with open('common/books_info.json', 'r') as f:
    books_info = json.load(f)


def extract_book():
    def save_slots_to_ctx_processing(
        ctx: Context,
        actor: Actor,
        *args,
        **kwargs,
    ) -> Context:
        slots = ctx.misc.get("slots", {})
        for book, info in books_info.items():
            pattern = re.compile(r"\b" + book, re.IGNORECASE)
            if bool(re.search(pattern, ctx.last_request.lower())):
                slots['author'] = info['author']
                slots['rating'] = info['rating']
                slots['description'] = info['description']
                slots['genres'] = info['genres']
                ctx.misc["slots"] = slots
                break

        return ctx

    return save_slots_to_ctx_processing