import logging
import json
import re
import random
import requests

from df_engine.core import Context, Actor

import common.dff.integration.context as int_ctx
import common.dff.integration.condition as int_cnd
from common.constants import CAN_NOT_CONTINUE, CAN_CONTINUE_SCENARIO, MUST_CONTINUE

logger = logging.getLogger(__name__)

with open(
    "data/stories.json",
) as stories_json:
    stories = json.load(stories_json)

with open(
    "data/phrases.json",
) as phrases_json:
    phrases = json.load(phrases_json)

STORYGPT_KEYWORDS_SERVICE_URL = "http://storygpt:8126/respond"
STORYGPT_SERVICE_URL = "http://prompt-storygpt:8127/respond"


def get_previous_node(ctx: Context) -> str:
    try:
        return [node_tuple[1] for node_tuple in ctx.labels.values()][-2]
    except Exception:
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
        return ""


def get_story_left(ctx: Context, actor: Actor) -> str:
    story_type = get_story_type(ctx, actor)
    stories_left = list(set(stories.get(story_type, [])) - set(ctx.misc.get("stories_told", [])))
    try:
        return random.choice(sorted(stories_left))
    except Exception:
        return ""


def choose_story(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    prev_node = get_previous_node(ctx)
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

    prev_node = get_previous_node(ctx)
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
    int_ctx.set_confidence(ctx, actor, 0.8) if int_cnd.is_do_not_know_vars(ctx, actor) else None
    story = ctx.misc.get("story", "")
    story_type = ctx.misc.get("story_type", "")

    return stories.get(story_type, {}).get(story, {}).get("punchline", "")


def fallback(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    prev_node = get_previous_node(ctx)
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
    else:
        int_ctx.set_can_continue(ctx, actor, MUST_CONTINUE)
        int_ctx.set_confidence(ctx, actor, 0.5) if int_cnd.is_do_not_know_vars(ctx, actor) else None
        return random.choice(sorted(phrases.get("start_phrases", [])))


def generate_story(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    int_ctx.set_confidence(ctx, actor, 0.9)
    int_ctx.set_can_continue(ctx, actor, CAN_CONTINUE_SCENARIO)
    reply = ''
    utt = int_ctx.get_last_human_utterance(ctx, actor)["text"]
    if utt:
        full_ctx = ctx.misc.get('agent', {}).get('dialog', {}).get('human_utterances', [])
        nouns = full_ctx[-1]['annotations']['rake_keywords']
        logger.info(f"Nouns: {full_ctx[-1]['annotations']['spacy_nounphrases']}")
        if len(full_ctx) > 1:
            nouns_tmp = full_ctx[-2]['annotations']['rake_keywords']
            nouns_tmp.extend(nouns)
            nouns = nouns_tmp
        logger.info(f"Keywords from annotator: {nouns}")
        ctx_texts = [c['text'] for c in full_ctx]
        logger.info(f"Contexts sent to StoryGPT service: {ctx_texts}")
        try:
            resp = requests.post(STORYGPT_KEYWORDS_SERVICE_URL, json={"utterances_histories": [[nouns]]}, timeout=300)
            raw_responses = resp.json()
        except Exception:
            return ''
        reply = raw_responses[0][0]
        reply = 'Oh, that reminded me of a story! ' + reply
    else:
        logger.info("No context")
    return reply


def choose_noun(nouns):
    for noun in nouns:
        if 'story' not in noun:
            return noun
    return ''


def choose_topic(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    int_ctx.set_can_continue(ctx, actor, MUST_CONTINUE)
    int_ctx.set_confidence(ctx, actor, 1.0)
    return "What do you want the story to be about?"


def generate_prompt_story(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    int_ctx.set_confidence(ctx, actor, 1.0)
    int_ctx.set_can_continue(ctx, actor, MUST_CONTINUE)
    utt = int_ctx.get_last_human_utterance(ctx, actor)["text"]
    logger.info(f'Utterance: {utt}')
    if utt:
        full_ctx = ctx.misc.get('agent', {}).get('dialog', {}).get('human_utterances', [])
        last_utt = full_ctx[-1]['text']
        nouns = full_ctx[-1].get('annotations', {}).get('spacy_nounphrases', [])
        logger.info(f'Nouns: {nouns}')

        final_noun = choose_noun(nouns)
        if "don't know" in last_utt or "not know" in last_utt \
                or "don't care" in last_utt or "not care" in last_utt:
            final_noun = 'cat'
        if not final_noun:
            final_noun = 'cat'
        final_noun = final_noun.split(' ')[-1].lower()
        logger.info(f'Final noun: {final_noun}')

        try:
            resp = requests.post(STORYGPT_SERVICE_URL, json={"utterances_histories": [[final_noun]]}, timeout=300)
            raw_responses = resp.json()
        except Exception:
            return ''
        logger.info(f"Skill receives from service: {raw_responses}")
        reply = raw_responses[0][0]
        reply = 'Ok,  ' + reply
    else:
        reply = ''
    return reply
