import logging
import re
from df_engine.core import Node, Context, Actor


logger = logging.getLogger(__name__)
# ....
book4genre = {"fantasy": "The Lord of the Rings by Tolkien", 
"historical": "he Twelve Rooms of the Nile by Enid Shomer", "dystopian": "We by Zamyatin"}


def extract_book_genre(node_label: str, node: Node, ctx: Context, actor: Actor, *args, **kwargs):
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
        slots["book_recommend"] = book4genre["fantasy"]
        ctx.misc["slots"] = slots
    elif re.findall(r'little prince', ctx.last_request, re.IGNORECASE) != []:
        slots["fav_book_genre"] = "dystopian"
        slots["book_recommend"] = book4genre["dystopian"]
        ctx.misc["slots"] = slots


    return node_label, node


def fill_slots(node_label: str, node: Node, ctx: Context, actor: Actor, *args, **kwargs):
    for slot_name, slot_value in ctx.misc.get("slots", {}).items():
        node.response = node.response.replace("{" f"{slot_name}" "}", slot_value)
    return node_label, node


def extract_fav_genre(node_label: str, node: Node, ctx: Context, actor: Actor, *args, **kwargs):
    slots = ctx.misc.get("slots", {})
    genres = ['fantasy', 'historical', 'dystopian']
    for genre in genres:
        if genre in ctx.last_request.lower():
            slots["fav_genre"] = genre
            slots["book_recommend"] = book4genre[genre]
            ctx.misc["slots"] = slots

    return node_label, node
