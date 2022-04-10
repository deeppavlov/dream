import re
import logging

from df_engine.core import Context, Actor

from common.dff.integration import condition as int_cnd

logger = logging.getLogger(__name__)
# ....


def example_lets_talk_about():
    def example_lets_talk_about_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        return int_cnd.is_lets_chat_about_topic_human_initiative(ctx, actor)

    return example_lets_talk_about_handler


def has_forbidden_words():
    def has_cond(ctx: Context, actor: Actor, *args, **kwargs):
        words = [
            "suicide",
            "death",
            "depressed",
            "kill myself",
            "die"
        ]

        words_re = "|".join(words)
        return bool(re.findall(words_re, ctx.last_request, re.IGNORECASE))
    
    return has_cond


def has_bad_day_words():
    def has_cond(ctx: Context, actor: Actor, *args, **kwargs):
        words = [
            "bad day",
            "awful day",
            "hard day"
            ]

        words_re = "|".join(words)
        return bool(re.findall(words_re, ctx.last_request, re.IGNORECASE))
    
    return has_cond


def has_relationship_words():
    def has_cond(ctx: Context, actor: Actor, *args, **kwargs):
        words = [
            "problem with",
            "problems with",
            "trouble with",
            "trouble with",
            'feel bad',
            'feel awful',
            'tired',
            'feel sad'
            ]

        words_re = "|".join(words)
        return bool(re.findall(words_re, ctx.last_request, re.IGNORECASE))
    
    return has_cond


def is_detailed():
    def has_cond(ctx: Context, actor: Actor, *args, **kwargs):
        # flag = False
        # if len(ctx.last_request) > 30:
        #     flag = True
        return bool(len(ctx.last_request) > 30)
        # return flag

    return has_cond


