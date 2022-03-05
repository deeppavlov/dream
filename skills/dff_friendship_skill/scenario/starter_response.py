import logging
import json
import random
import sentry_sdk
from os import getenv

import common.dff.integration.context as int_ctx
from common.constants import MUST_CONTINUE, CAN_CONTINUE_PROMPT
from common.music import OPINION_REQUESTS_ABOUT_MUSIC
from common.starter import (
    INTROS,
    OUTROS,
    CATEGORIES_VERBS,
    PERSONA1_GENRES,
    GENRES_ATTITUDES,
    GENRE_ITEMS,
    WEEKDAYS_ATTITUDES,
    WHATS_YOUR_FAV_PHRASES,
    WHY_QUESTIONS,
    ACKNOWLEDGEMENTS,
    MY_FAV_ANSWERS,
    WONDER_WHY_QUESTIONS,
    OH_PHRASES,
    SO_YOU_SAY_PHRASES,
    ASSENT_YES_PHRASES,
    ASSENT_NO_PHRASES,
)
from df_engine.core import Actor, Context

sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

with open("common/topic_favorites.json", "r") as f:
    FAV_STORIES_TOPICS = json.load(f)

CONF_HIGH = 1.0
CONF_MIDDLE = 0.95
CONF_LOW = 0.9


def genre_response(ctx: Context, actor: Actor) -> str:
    shared_memory = int_ctx.get_shared_memory(ctx, actor)
    used_categories = shared_memory.get("used_categories", [])
    # _object = ""
    category = random.choice(list(PERSONA1_GENRES))
    category_verb = CATEGORIES_VERBS.get(category, "")
    genre = random.choice(PERSONA1_GENRES.get(category, [""]))
    attitude = random.choice(GENRES_ATTITUDES.get(genre, [""]))
    item = random.choice(GENRE_ITEMS.get(genre, [""]))

    # if category in CATEGORIES_OBJECTS:
    #     _object = random.choice(CATEGORIES_OBJECTS[category])
    # item = FAV_STORIES_TOPICS.get(category, "").get("name", "")
    # if item:
    #     category_verb = CATEGORIES_VERBS.get(category, "")
    #     genre = shared.get_genre_top_wiki_parser(_object, item)[0]
    #     attitude = random.choice(GENRES_ATTITUDES.get(genre, [""]))
    #     int_ctx.save_to_shared_memory(ctx, actor, used_categories=used_categories + [category])
    if all([category_verb, genre, attitude, item]):
        int_ctx.set_confidence(ctx, actor, confidence=CONF_HIGH)
        int_ctx.set_can_continue(ctx, actor, continue_flag=MUST_CONTINUE)
        int_ctx.save_to_shared_memory(
            ctx, actor, used_categories=used_categories + [{"category": category, "genre": genre, "item": item}]
        )
        return (
            f"{random.choice(INTROS)} "
            + f"{category_verb} {item}. {attitude} {random.choice(OUTROS)} {genre} {category}?"
        )
    else:
        int_ctx.set_confidence(ctx, actor, 0)
        return ""


def what_fav_response(ctx: Context, actor: Actor) -> str:
    shared_memory = int_ctx.get_shared_memory(ctx, actor)
    used_topics = shared_memory.get("used_categories", [])
    curr_topic = ""
    curr_genre = ""
    if used_topics:
        curr_topic = used_topics[-1].get("category", "")
        curr_genre = used_topics[-1].get("genre", "")
    if curr_topic:
        int_ctx.set_confidence(ctx, actor, confidence=CONF_HIGH)
        int_ctx.set_can_continue(ctx, actor, continue_flag=CAN_CONTINUE_PROMPT)
        if curr_topic == "music":
            return random.choice(OPINION_REQUESTS_ABOUT_MUSIC)
        return f"{random.choice(WHATS_YOUR_FAV_PHRASES)} {curr_genre} {curr_topic}?"
    else:
        int_ctx.set_confidence(ctx, actor, 0)
        return ""


def why_response(ctx: Context, actor: Actor) -> str:
    int_ctx.set_confidence(ctx, actor, confidence=CONF_HIGH)
    int_ctx.set_can_continue(ctx, actor, continue_flag=MUST_CONTINUE)
    return f"{random.choice(WHY_QUESTIONS)}"


def my_fav_response(ctx: Context, actor: Actor) -> str:
    shared_memory = int_ctx.get_shared_memory(ctx, actor)
    used_topics = shared_memory.get("used_categories", [])
    if used_topics:
        category = used_topics[-1].get("category", "")
        item = FAV_STORIES_TOPICS.get(category, "").get("name", "")
        if category not in ["series", "music"]:
            category += "s"
        if item:
            int_ctx.set_confidence(ctx, actor, confidence=CONF_HIGH)
            int_ctx.set_can_continue(ctx, actor, continue_flag=MUST_CONTINUE)
            return (
                f"{random.choice(ACKNOWLEDGEMENTS)}"
                + random.choice(MY_FAV_ANSWERS(category, item))
                + f"{random.choice(WONDER_WHY_QUESTIONS)}"
            )
    else:
        int_ctx.set_confidence(ctx, actor, 0)
        return ""


def repeat_response(ctx: Context, actor: Actor) -> str:
    utt = int_ctx.get_last_human_utterance(ctx, actor)["text"].lower()
    int_ctx.set_confidence(ctx, actor, confidence=CONF_HIGH)
    int_ctx.set_can_continue(ctx, actor, continue_flag=MUST_CONTINUE)
    return f"{random.choice(OH_PHRASES)} " + random.choice(SO_YOU_SAY_PHRASES(utt))


def assent_yes_response(ctx: Context, actor: Actor) -> str:
    int_ctx.set_confidence(ctx, actor, confidence=CONF_HIGH)
    int_ctx.set_can_continue(ctx, actor, continue_flag=MUST_CONTINUE)
    return random.choice(ASSENT_YES_PHRASES)


def assent_no_response(ctx: Context, actor: Actor) -> str:
    int_ctx.set_confidence(ctx, actor, confidence=CONF_HIGH)
    int_ctx.set_can_continue(ctx, actor, continue_flag=MUST_CONTINUE)
    return random.choice(ASSENT_NO_PHRASES)


def my_fav_story_response(ctx: Context, actor: Actor) -> str:
    shared_memory = int_ctx.get_shared_memory(ctx, actor)
    used_categories = shared_memory.get("used_categories", [])
    story = ""
    if used_categories:
        category = used_categories[-1].get("category", "")
        story = FAV_STORIES_TOPICS.get(category, "").get("story", "")
        if story:
            int_ctx.set_confidence(ctx, actor, confidence=CONF_HIGH)
            int_ctx.set_can_continue(ctx, actor, continue_flag=MUST_CONTINUE)
            return story
    else:
        int_ctx.set_confidence(ctx, actor, 0)
        return ""


def weekday_response(ctx: Context, actor: Actor) -> str:
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekday = ""
    attitude = ""
    shared_memory = int_ctx.get_shared_memory(ctx, actor)
    used_categories = shared_memory.get("used_categories", [])
    category = "day"
    int_ctx.save_to_shared_memory(ctx, actor, used_categories=used_categories + [category])
    weekday = weekdays[int(datetime.datetime.now(pytz.timezone("US/Mountain")).weekday()) - 1]
    attitude = WEEKDAYS_ATTITUDES.get(weekday, "")
    if weekday and attitude:
        int_ctx.set_confidence(ctx, actor, confidence=CONF_HIGH)
        int_ctx.set_can_continue(ctx, actor, continue_flag=MUST_CONTINUE)
        return f"Oh, Gosh, it's {weekday}! {attitude} What's your favorite day of the week?"
    else:
        int_ctx.set_confidence(ctx, actor, 0)
        return ""


def friday_response(ctx: Context, actor: Actor) -> str:
    utt = int_ctx.get_last_human_utterance(ctx, actor)["text"].lower()
    friday_check = "friday" in utt
    weekday = ""
    if friday_check:
        int_ctx.set_confidence(ctx, actor, confidence=CONF_HIGH)
        int_ctx.set_can_continue(ctx, actor, continue_flag=MUST_CONTINUE)
        return "It's my favorite too!"
    else:
        for day in WEEKDAYS_ATTITUDES:
            if day in utt:
                weekday = day
                break
        if weekday:
            attitude = WEEKDAYS_ATTITUDES.get(weekday, "")
            if attitude:
                int_ctx.set_confidence(ctx, actor, confidence=CONF_MIDDLE)
                int_ctx.set_can_continue(ctx, actor, continue_flag=CAN_CONTINUE_PROMPT)
                return f"Ah, interesting. I {attitude}. Why do you like it?"
        else:
            int_ctx.set_confidence(ctx, actor, confidence=CONF_MIDDLE)
            int_ctx.set_can_continue(ctx, actor, continue_flag=CAN_CONTINUE_PROMPT)
            return "Okay. But why?"


def my_fav_day_response(ctx: Context, actor: Actor) -> str:
    int_ctx.set_confidence(ctx, actor, confidence=CONF_HIGH)
    int_ctx.set_can_continue(ctx, actor, continue_flag=MUST_CONTINUE)
    return "Aha. Speaking of me, my favorite day is Friday. " "As the song says, Nothing matters like the weekend."
