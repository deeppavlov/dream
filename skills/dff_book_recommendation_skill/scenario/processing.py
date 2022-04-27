import logging
import re
import json

from df_engine.core import Node, Context, Actor


logger = logging.getLogger(__name__)
# ....

with open('common/genre2books.json', 'r') as f:
    genre2books = json.load(f)

with open('common/book2genre.json', 'r') as f:
    book2genre = json.load(f)


def extract_book_genre():
    def save_slots_to_ctx_processing(
        ctx: Context,
        actor: Actor,
        *args,
        **kwargs,
    ) -> Context:
        slots = ctx.misc.get("slots", {})
        for book in book2genre.keys():
            if book in ctx.last_request.lower():
                slots["fav_book_genre"] = book2genre[book]
                if book not in genre2books[book2genre[book]][0].lower():
                    slots["book_recommend"] = genre2books[book2genre[book]][0]
                else:
                    slots["book_recommend"] = genre2books[book2genre[book]][1]
                ctx.misc["slots"] = slots
                break

        return ctx

    return save_slots_to_ctx_processing


def extract_fav_genre():
    def save_slots_to_ctx_processing(
        ctx: Context,
        actor: Actor,
        *args,
        **kwargs,
    ) -> Context:
        slots = ctx.misc.get("slots", {})
        for genre in genre2books.keys():
            if genre in ctx.last_request.lower():
                slots["fav_genre"] = genre
                slots["book_recommend_1"] = genre2books[genre][0]
                slots["book_recommend_2"] = genre2books[genre][1]
                slots["book_recommend_3"] = genre2books[genre][2]
                ctx.misc["slots"] = slots

        return ctx
    
    return save_slots_to_ctx_processing
