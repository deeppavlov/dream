import logging
import re
import os
from . import response as loc_rsp

from df_engine.core import Context, Actor

import common.dff.integration.context as int_ctx

logging.basicConfig(format="%(asctime)s - %(pathname)s - %(lineno)d - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)
logging.getLogger("werkzeug").setLevel("WARNING")

STORY_TYPE = os.getenv("STORY_TYPE")


def has_story_type(ctx: Context, actor: Actor) -> bool:
    return bool(loc_rsp.get_story_type(ctx, actor))


def has_story_left(ctx: Context, actor: Actor) -> bool:
    return bool(loc_rsp.get_story_left(ctx, actor))


def is_tell_me_a_story(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    return bool(
        re.search("tell", ctx.last_request, re.IGNORECASE) and re.search("story", ctx.last_request, re.IGNORECASE)
    )


def is_asked_for_a_story(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    prev_node = loc_rsp.get_previous_node(ctx)
    return prev_node != "which_story_node"


def needs_scripted_story(ctx: Context, actor: Actor) -> bool:
    if STORY_TYPE == 'scripted':
        return True
    return False


def has_story_intent(ctx: Context, actor: Actor) -> bool:
    utt = int_ctx.get_last_human_utterance(ctx, actor)
    if utt["text"]:
        story_intent = utt['annotations']['intent_catcher']['tell_me_a_story']['detected']
        logger.info(f"Story intent value: {story_intent}")
        if story_intent == 1:
            return True
    return False


def prev_is_story(ctx: Context, actor: Actor) -> bool:
    utt = int_ctx.get_last_bot_utterance(ctx, actor)
    if utt["text"]:
        if utt["text"].startswith('Oh, that reminded me of a story!') \
                or utt["text"].startswith('Ok, Let me tell you a story about'):
            return True
    return False


def asks_more(ctx: Context, actor: Actor) -> bool:
    utt = int_ctx.get_last_human_utterance(ctx, actor)
    more_phrases = ['more', 'tell me more', 'continue', 'more stories', 'tell me more stories', 'one more story']
    if utt["text"]:
        if utt["text"].lower().strip() in more_phrases:
            return True
    return False


def should_return(ctx: Context, actor: Actor) -> bool:
    if prev_is_story(ctx, actor):
        if asks_more(ctx, actor):
            return True
        else:
            return False
    else:
        return True


def prev_is_question(ctx: Context, actor: Actor) -> bool:
    utt = int_ctx.get_last_bot_utterance(ctx, actor)
    if utt["text"]:
        if "What do you want the story to be about?" in utt["text"]:
            return True
    return False


def has_five_keywords(ctx: Context, actor: Actor):
    utt = int_ctx.get_last_bot_utterance(ctx, actor)
    if utt["text"]:
        utterances = int_ctx.get_human_utterances(ctx, actor)
        if len(utterances) > 1:
            nouns = utterances[-1]["annotations"].get('rake_keywords', [])
            nouns.extend(utterances[-2]["annotations"].get('rake_keywords', []))
            if len(nouns) >= 5:
                return True
    return False
