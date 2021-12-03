import logging
import json
import re
import random

from dff.core import Context, Actor

import common.dff.integration.context as int_ctx
import common.dff.integration.condition as int_cnd

logger = logging.getLogger(__name__)

with open(
    "data/stories.json",
) as stories_json:
    stories = json.load(stories_json)

with open(
    "data/phrases.json",
) as phrases_json:
    phrases = json.load(phrases_json)


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
        int_ctx.set_can_continue(ctx, actor, "MUST_CONTINUE")

        # include sure if user asked to tell a story, include nothing if agent proposed to tell a story
        sure_phrase = random.choice(sorted(phrases.get("sure", []))) if prev_node == "start_node" else ""
        return sure_phrase + " " + random.choice(sorted(phrases.get("which_story", [])))
    elif prev_node == "choose_story_node":
        int_ctx.set_can_continue(ctx, actor, "CANNOT_CONTINUE")
        return random.choice(sorted(phrases.get("no", [])))
    else:
        return "Ooops."


def tell_punchline(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    int_ctx.set_can_continue(ctx, actor, "CAN_CONTINUE")
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
        int_ctx.set_can_continue(ctx, actor, "CANNOT_CONTINUE")
        return "Oh, sorry, but I've run out of stories."

    # no stories
    elif prev_node == "which_story_node" and not story_type:
        int_ctx.set_can_continue(ctx, actor, "CAN_CONTINUE")
        return random.choice(sorted(phrases.get("no_stories", [])))

    # if prev_node is tell_punchline_node or fallback_node
    else:
        int_ctx.set_can_continue(ctx, actor, "MUST_CONTINUE")
        int_ctx.set_confidence(ctx, actor, 0.5) if int_cnd.is_do_not_know_vars(ctx, actor) else None
        return random.choice(sorted(phrases.get("start_phrases", [])))
