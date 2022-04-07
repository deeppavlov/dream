import logging
import re
from df_engine.core import Node, Context, Actor


logger = logging.getLogger(__name__)
# ....
book4genre = {"fantasy": "The Lord of the Rings by Tolkien", 
"historical": "he Twelve Rooms of the Nile by Enid Shomer", "dystopian": "We by Zamyatin"}


def extract_book_genre():
    def save_slots_to_ctx_processing(
        ctx: Context,
        actor: Actor,
        *args,
        **kwargs,
    ) -> Context:
        slots = ctx.misc.get("slots", {})
        books = ['harry potter', 'war and peace', '1984']
        books_re = "|".join(books)
        extracted_book = re.findall(books_re, ctx.last_request, re.IGNORECASE)
        if re.findall(r'harry potter', ctx.last_request, re.IGNORECASE) != []:
            slots["fav_book_genre"] = "fantasy"
            slots["book_recommend"] = book4genre["fantasy"]
            ctx.misc["slots"] = slots
        elif re.findall(r'war and peace', ctx.last_request, re.IGNORECASE) != []:
            slots["fav_book_genre"] = "historical"
            slots["book_recommend"] = book4genre["historical"]
            ctx.misc["slots"] = slots
        elif re.findall(r'1984', ctx.last_request, re.IGNORECASE) != []:
            slots["fav_book_genre"] = "dystopian"
            slots["book_recommend"] = book4genre["dystopian"]
            ctx.misc["slots"] = slots

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
        genres = ['fantasy', 'historical', 'dystopian']
        for genre in genres:
            if genre in ctx.last_request.lower():
                slots["fav_genre"] = genre
                slots["book_recommend"] = book4genre[genre]
                ctx.misc["slots"] = slots

        return ctx
    
    return save_slots_to_ctx_processing
