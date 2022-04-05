import logging
import re

from df_engine.core import Context, Actor

from common.dff.integration import condition as int_cnd

logger = logging.getLogger(__name__)
# ....

books = ['harry potter', 'war and peace', 'little prince']
appreciate_words = ['my favorite', 'my fav', 'my favourite', 'i love', 'i like']
genres = ['fantasy', 'historical novels', 'parables']

def example_lets_talk_about():
    def example_lets_talk_about_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        return int_cnd.is_lets_chat_about_topic_human_initiative(ctx, actor)

    return example_lets_talk_about_handler


def mentioned_book(ctx: Context, actor: Actor, *args, **kwargs):
    words_re = "|".join(books)
    return bool(re.findall(words_re, ctx.last_request, re.IGNORECASE))


def mentioned_fav(ctx: Context, actor: Actor, *args, **kwargs):
    words_re = "|".join(appreciate_words)
    return bool(re.findall(words_re, ctx.last_request, re.IGNORECASE))


def mentioned_genre(ctx: Context, actor: Actor, *args, **kwargs):
    genres_re = "|".join(genres)
    return bool(re.findall(genres_re, ctx.last_request, re.IGNORECASE))
