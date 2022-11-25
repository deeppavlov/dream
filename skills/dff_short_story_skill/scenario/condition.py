import logging
import re
import os
from . import response as loc_rsp

from df_engine.core import Context, Actor

import common.dff.integration.context as int_ctx
from common.short_story import STORY_TOPIC_QUESTIONS
from common.utils import get_intents, is_question, is_special_factoid_question

logging.basicConfig(format="%(asctime)s - %(pathname)s - %(lineno)d - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)
logging.getLogger("werkzeug").setLevel("WARNING")

STORY_TYPE = os.getenv("STORY_TYPE", "generated")
more_stories_pattern = re.compile(r"^(((tell\s(me\s)*)|(one\s))*more(\sstor((y)|(ies)))*)[.,!?;]*$", re.IGNORECASE)
prev_question_pattern_tmp = "(" + ")|(".join(STORY_TOPIC_QUESTIONS) + ")"
prev_question_pattern_tmp = prev_question_pattern_tmp.replace("?", r"\?")
prev_question_pattern = re.compile(f"{prev_question_pattern_tmp}", re.IGNORECASE)


def has_story_type(ctx: Context, actor: Actor) -> bool:
    return bool(loc_rsp.get_story_type(ctx, actor))


def has_story_left(ctx: Context, actor: Actor) -> bool:
    return bool(loc_rsp.get_story_left(ctx, actor))


def is_tell_me_a_story(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    return bool(
        re.search("tell", ctx.last_request, re.IGNORECASE) and re.search("story", ctx.last_request, re.IGNORECASE)
    )


def is_asked_for_a_story(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    prev_node = loc_rsp.get_previous_node(ctx, actor)
    return prev_node != "which_story_node"


def needs_scripted_story(ctx: Context, actor: Actor) -> bool:
    if STORY_TYPE == "scripted":
        return True
    return False


def has_story_intent(ctx: Context, actor: Actor) -> bool:
    utt = int_ctx.get_last_human_utterance(ctx, actor)
    if utt.get("text", ""):
        intents = get_intents(utt)
        logger.info(f"Detected Intents: {intents}")
        if "tell_me_a_story" in intents:
            return True
    return False


def prev_is_story(ctx: Context, actor: Actor) -> bool:
    utt = int_ctx.get_last_bot_utterance(ctx, actor)
    if utt.get("text", ""):
        if utt["text"].startswith("Oh, that reminded me of a story!") or utt["text"].startswith(
            "Ok,  Let me share a story"
        ):
            return True
    return False


def asks_more(ctx: Context, actor: Actor) -> bool:
    utt = int_ctx.get_last_human_utterance(ctx, actor)
    if utt.get("text", ""):
        text = utt["text"]
        if more_stories_pattern.match(text):
            return True
    return False


def should_return(ctx: Context, actor: Actor) -> bool:
    if prev_is_story(ctx, actor):
        if asks_more(ctx, actor):
            logger.info("Should return is True")
            return True
        else:
            return False
    else:
        logger.info("Should return is True")
        return True


def prev_is_story_topic_question(ctx: Context, actor: Actor) -> bool:
    utt = int_ctx.get_last_bot_utterance(ctx, actor)
    if utt.get("text", ""):
        if prev_question_pattern.search(utt["text"]):
            return True
    return False


def has_five_keywords(ctx: Context, actor: Actor):
    utt = int_ctx.get_last_bot_utterance(ctx, actor)
    if utt.get("text", ""):
        utterances = int_ctx.get_human_utterances(ctx, actor)
        if len(utterances) > 1:
            nouns = utterances[-1].get("annotations", {}).get("rake_keywords", [])
            nouns.extend(utterances[-2].get("annotations", {}).get("rake_keywords", []))
            if len(nouns) >= 5:
                return True
    return False


def prev_is_any_question(ctx: Context, actor: Actor) -> bool:
    utt = int_ctx.get_last_human_utterance(ctx, actor)
    text = utt.get("text", "")
    if is_question(text) or is_special_factoid_question(utt):
        return True
    return False
