import logging
import json
import re
import random
import requests
import os

from df_engine.core import Context, Actor

import common.dff.integration.context as int_ctx
import common.dff.integration.condition as int_cnd
from common.constants import CAN_NOT_CONTINUE, CAN_CONTINUE_SCENARIO, MUST_CONTINUE
from common.short_story import STORY_TOPIC_QUESTIONS
from common.utils import get_entities, get_intents
import sentry_sdk

logger = logging.getLogger(__name__)

care_pattern = re.compile(r"(don't|(do not)) (care|know)", re.IGNORECASE)
story_pattern = re.compile(r"\bstory\b", re.IGNORECASE)

with open(
    "data/stories.json",
) as stories_json:
    stories = json.load(stories_json)

with open(
    "data/phrases.json",
) as phrases_json:
    phrases = json.load(phrases_json)

PROMPT_STORYGPT_SERVICE_URL = os.getenv("PROMPT_STORYGPT_SERVICE_URL", "http://prompt-storygpt:8127/respond")
STORYGPT_SERVICE_URL = os.getenv("STORYGPT_SERVICE_URL", "http://storygpt:8126/respond")


def get_previous_node(ctx: Context, actor: Actor) -> str:
    utt = int_ctx.get_last_human_utterance(ctx, actor)
    last_utt = utt.get("text", "")
    if last_utt:
        try:
            return [node_tuple[1] for node_tuple in ctx.labels.values()][-2]
        except Exception as exc:
            logger.exception(exc)
            sentry_sdk.capture_exception(exc)
            return "start_node"
    else:
        return "start_node"


def get_story_type(ctx: Context, actor: Actor) -> str:
    human_sentence = ctx.last_request
    if re.search("fun((ny)|(niest)){0,1}", human_sentence):
        return "funny"
    elif re.search("(horror)|(scary)|(frightening)|(spooky)", human_sentence):
        return "scary"
    elif re.search(
        "(bedtime)|(good)|(kind)|(baby)|(children)|(good night)|(for kid(s){0,1})",
        human_sentence,
    ):
        return "bedtime"
    else:
        return "funny"


def get_story_left(ctx: Context, actor: Actor) -> str:
    story_type = get_story_type(ctx, actor)
    stories_left = list(set(stories.get(story_type, [])) - set(ctx.misc.get("stories_told", [])))
    try:
        return random.choice(sorted(stories_left))
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return ""


def choose_story(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    prev_node = get_previous_node(ctx, actor)
    story = get_story_left(ctx, actor)
    story_type = get_story_type(ctx, actor)
    setup = stories.get(story_type, {}).get(story, {}).get("setup", "")
    what_happend_next_phrase = random.choice(sorted(phrases.get("what_happend_next", [])))

    # include sure if user defined a type of story at the beginnig, otherwise include nothing
    sure_phrase = random.choice(sorted(phrases.get("sure", []))) if prev_node == "start_node" else ""

    ctx.misc["stories_told"] = ctx.misc.get("stories_told", []) + [story]
    ctx.misc["story"] = story
    ctx.misc["story_type"] = story_type

    return sure_phrase + " " + setup + " " + "..." + " " + what_happend_next_phrase


def which_story(ctx: Context, actor: Actor, *args, **kwargs) -> str:

    prev_node = get_previous_node(ctx, actor)
    if prev_node in ["start_node", "fallback_node"]:
        int_ctx.set_can_continue(ctx, actor, MUST_CONTINUE)

        # include sure if user asked to tell a story, include nothing if agent proposed to tell a story
        sure_phrase = random.choice(sorted(phrases.get("sure", []))) if prev_node == "start_node" else ""
        return sure_phrase + " " + random.choice(sorted(phrases.get("which_story", [])))
    elif prev_node == "choose_story_node":
        int_ctx.set_can_continue(ctx, actor, CAN_NOT_CONTINUE)
        return random.choice(sorted(phrases.get("no", [])))
    else:
        return "Ooops."


def tell_punchline(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    int_ctx.set_can_continue(ctx, actor, CAN_CONTINUE_SCENARIO)
    if int_cnd.is_do_not_know_vars(ctx, actor):
        int_ctx.set_confidence(ctx, actor, 0.8)
    else:
        int_ctx.set_confidence(ctx, actor, 0.0)
    story = ctx.misc.get("story", "")
    story_type = ctx.misc.get("story_type", "")

    return stories.get(story_type, {}).get(story, {}).get("punchline", "")


def fallback(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    prev_node = get_previous_node(ctx, actor)
    story_type = get_story_type(ctx, actor)
    story_left = get_story_left(ctx, actor)

    # runout stories
    if prev_node == "which_story_node" and story_type and not story_left:
        int_ctx.set_can_continue(ctx, actor, CAN_NOT_CONTINUE)
        return "Oh, sorry, but I've run out of stories."

    # no stories
    elif prev_node == "which_story_node" and not story_type:
        int_ctx.set_can_continue(ctx, actor, CAN_CONTINUE_SCENARIO)
        return random.choice(sorted(phrases.get("no_stories", [])))

    # if prev_node is tell_punchline_node or fallback_node
    elif prev_node == "tell_punchline_node" or prev_node == "fallback_node":
        int_ctx.set_can_continue(ctx, actor, MUST_CONTINUE)
        if int_cnd.is_do_not_know_vars(ctx, actor):
            int_ctx.set_confidence(ctx, actor, 0.5)
        else:
            int_ctx.set_confidence(ctx, actor, 0.0)
        return random.choice(sorted(phrases.get("start_phrases", [])))

    # for generated story scenarios
    else:
        int_ctx.set_can_continue(ctx, actor, CAN_NOT_CONTINUE)
        return ""


def generate_story(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    reply = ""
    utt = int_ctx.get_last_human_utterance(ctx, actor)["text"]
    if utt:
        full_ctx = int_ctx.get_human_utterances(ctx, actor)
        nouns = full_ctx[-1].get("annotations", {}).get("rake_keywords", [])
        if len(full_ctx) > 1:
            nouns_tmp = full_ctx[-2].get("annotations", {}).get("rake_keywords", [])
            nouns_tmp.extend(nouns)
            nouns = nouns_tmp
        logger.info(f"Keywords from annotator: {nouns}")
        try:
            resp = requests.post(STORYGPT_SERVICE_URL, json={"utterances_histories": [[nouns]]}, timeout=3)
            raw_responses = resp.json()
            int_ctx.set_confidence(ctx, actor, 0.9)
            # CAN_NOT_CONTINUE because it's the last utterance in the scenario
            int_ctx.set_can_continue(ctx, actor, CAN_NOT_CONTINUE)
        except Exception as exc:
            logger.exception(exc)
            sentry_sdk.capture_exception(exc)
            int_ctx.set_confidence(ctx, actor, 0.0)
            int_ctx.set_can_continue(ctx, actor, CAN_NOT_CONTINUE)
            return ""
        reply = raw_responses[0][0]
        reply = "Oh, that reminded me of a story! " + reply
        logger.info(reply)
    else:
        int_ctx.set_confidence(ctx, actor, 0.0)
        int_ctx.set_can_continue(ctx, actor, CAN_NOT_CONTINUE)
        logger.info("No context")
    return reply


def choose_noun(nouns):
    for noun in nouns:
        story_word = re.search(story_pattern, noun)
        if not story_word:
            return noun
    return ""


def choose_topic(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    int_ctx.set_can_continue(ctx, actor, MUST_CONTINUE)
    int_ctx.set_confidence(ctx, actor, 1.0)
    return random.choice(STORY_TOPIC_QUESTIONS)


def generate_prompt_story(ctx: Context, actor: Actor, first=True, *args, **kwargs) -> str:
    utt = int_ctx.get_last_human_utterance(ctx, actor)
    last_utt = utt.get("text", "")
    logger.info(f"Utterance: {last_utt}")
    if last_utt:
        if first:
            nouns = get_entities(utt, only_named=False, with_labels=False)
            logger.info(f"Found entities: {nouns}")
            final_noun = choose_noun(nouns)
            if care_pattern.search(last_utt):
                final_noun = "cat"
                logger.info(f"Final noun: {final_noun}, because User doesn't know the topic or doesn't care")
            if not final_noun:
                final_noun = "cat"
                logger.info(f"Final noun: {final_noun}, because User didn't suggest noun for the topic")
            else:
                final_noun = final_noun.split(" ")[-1].lower()
                logger.info(f"Final noun: {final_noun}")
            service_input = final_noun
        else:
            bot_utt = int_ctx.get_last_bot_utterance(ctx, actor)
            service_input = bot_utt.get("text", "")
            logger.info(f"Previous story part: {service_input}")
        try:
            resp = requests.post(
                PROMPT_STORYGPT_SERVICE_URL, json={"utterances_histories": [[service_input], first]}, timeout=3
            )
            raw_responses = resp.json()
        except requests.exceptions.Timeout:
            logger.info("Prompt StoryGPT service timeout.")
            if first:
                sorry_message = (
                    f"Sorry, can't remember any stories about {service_input}! "
                    f"Maybe you can tell me something about {service_input}?"
                )
            else:
                sorry_message = "Sorry, I suddenly forgot what happened next! " "Maybe you can continue my story?"
            int_ctx.set_confidence(ctx, actor, 0.0)
            int_ctx.set_can_continue(ctx, actor, CAN_NOT_CONTINUE)
            logger.info(f"Sorry message: {sorry_message}")
            return sorry_message
        except Exception as exc:
            logger.exception(exc)
            sentry_sdk.capture_exception(exc)
            int_ctx.set_confidence(ctx, actor, 0.0)
            int_ctx.set_can_continue(ctx, actor, CAN_NOT_CONTINUE)
            return ""
        logger.info(f"Skill receives from service: {raw_responses}")
        reply = raw_responses[0][0]
        # confidence for this is set in the next functions
        # int_ctx.set_confidence(ctx, actor, 1.0)
        # int_ctx.set_can_continue(ctx, actor, MUST_CONTINUE)
    else:
        reply = ""
        int_ctx.set_confidence(ctx, actor, 0.0)
        int_ctx.set_can_continue(ctx, actor, CAN_NOT_CONTINUE)
    return reply


def generate_first_prompt_part(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    reply = generate_prompt_story(ctx, actor, first=True)
    if reply:
        int_ctx.set_confidence(ctx, actor, 1.0)
        # MUST_CONTINUE because we need to finish it, if user agrees
        int_ctx.set_can_continue(ctx, actor, MUST_CONTINUE)
    else:
        int_ctx.set_confidence(ctx, actor, 0.0)
        int_ctx.set_can_continue(ctx, actor, CAN_NOT_CONTINUE)
    return reply


def generate_second_prompt_part(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    # if answer is not NO and not YES, set lower confidence
    utt = int_ctx.get_last_human_utterance(ctx, actor)
    intents = get_intents(utt, probs=False, which="intent_catcher")
    reply_conf = 0.5
    if "yes" in intents:
        reply_conf = 1.0

    # check if prev utterance was first part of the story (just in case)
    bot_utt = int_ctx.get_last_bot_utterance(ctx, actor)
    last_utt = bot_utt.get("text", "")
    if not last_utt.startswith("Ok,  Let me share a story"):
        int_ctx.set_confidence(ctx, actor, 0.0)
        int_ctx.set_can_continue(ctx, actor, CAN_NOT_CONTINUE)
        logger.info(f"Previous Bot Utterance wasn't a Story: {last_utt}")
        return ""

    reply = generate_prompt_story(ctx, actor, first=False)
    if reply:
        int_ctx.set_confidence(ctx, actor, reply_conf)
        # not MUST_CONTINUE because it's the last part
        int_ctx.set_can_continue(ctx, actor, CAN_CONTINUE_SCENARIO)
    else:
        int_ctx.set_confidence(ctx, actor, 0.0)
        int_ctx.set_can_continue(ctx, actor, CAN_NOT_CONTINUE)
    return reply


def suggest_more_stories(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    # if answer is not NO and not YES, set lower confidence
    utt = int_ctx.get_last_human_utterance(ctx, actor)
    intents = get_intents(utt, probs=False, which="intent_catcher")
    reply_conf = 0.5
    if "yes" in intents:
        reply_conf = 0.7

    reply = "Would you like another story?"
    int_ctx.set_confidence(ctx, actor, reply_conf)
    # CAN_CONTINUE_SCENARIO because if yes we should continue gpt_prompt scenario
    int_ctx.set_can_continue(ctx, actor, CAN_CONTINUE_SCENARIO)
    return reply
