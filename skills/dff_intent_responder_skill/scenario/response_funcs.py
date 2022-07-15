#!/usr/bin/env python
import logging
import json
import random
import re
from datetime import datetime
from os import getenv

import common.dff.integration.context as int_ctx
from common.utils import get_entities
from df_engine.core import Actor, Context


INTENT_RESPONSE_PHRASES_FNAME = getenv("INTENT_RESPONSE_PHRASES_FNAME", "intent_response_phrases.json")
LANGUAGE = getenv("LANGUAGE", "EN")
logging.basicConfig(format="%(asctime)s - %(pathname)s - %(lineno)d - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.info(f"Intent response phrases are from file: {INTENT_RESPONSE_PHRASES_FNAME}")

with open(f"scenario/data/{INTENT_RESPONSE_PHRASES_FNAME}", "r") as fp:
    RESPONSES = json.load(fp)

WHERE_ARE_YOU_FROM = {"EN": "Where are you from?", "RU": "Откуда ты родом?"}
WHERE_ARE_YOU_NOW = {"EN": "What is your location?", "RU": "А где ты сейчас живешь?"}
DIDNOT_SAY_ANYTHING = {"EN": "I did not say anything!", "RU": "А я ничего и не говорила."}


def repeat_respond(ctx: Context, actor: Actor, intention: str):
    utterances_bot = int_ctx.get_bot_utterances(ctx, actor)
    utterances_human = get_human_utterances(ctx, actor)
    WHAT_BOT_PHRASES = ["did i say something confusing", "you sound shocked", "if you want me to repeat"]
    bot_phrases = [utt.get("text", "") if isinstance(utt, dict) else utt for utt in utterances_bot]
    if len(utterances_human) >= 2:
        responder_phrase = utterances_human[-2]["text"].lower()
        if any([bot_ptrn in responder_phrase for bot_ptrn in WHAT_BOT_PHRASES]):
            bot_utt = ""
            for bot_phrase in bot_phrases[::-1]:
                if bot_phrase != bot_phrases[-1]:
                    bot_utt = bot_phrase
                    break
        else:
            bot_utt = utterances_human[-2]["text"]
    else:
        bot_utt = ""
    return bot_utt if len(bot_utt) > 0 else DIDNOT_SAY_ANYTHING[LANGUAGE]


def where_are_you_from_respond(ctx: Context, actor: Actor, intention: str):
    response_phrases = RESPONSES[intention]
    dialog = int_ctx.get_dialog(ctx, actor)
    human_profile_exists = "human" in dialog and "profile" in dialog["human"]

    already_known_user_property = None
    if human_profile_exists:
        already_known_user_property = dialog["human"]["profile"].get("homeland", None)
    if already_known_user_property is None:
        response = f"{random.choice(response_phrases).strip()} {WHERE_ARE_YOU_FROM[LANGUAGE]}"
    else:
        already_known_user_property = dialog["human"]["profile"].get("location", None)
        if already_known_user_property is None:
            response = f"{random.choice(response_phrases).strip()} {WHERE_ARE_YOU_NOW[LANGUAGE]}"
        else:
            response = random.choice(response_phrases).strip()
    return response


def random_respond(ctx: Context, actor: Actor, intention: str):
    response_phrases = RESPONSES[intention]
    dialog = int_ctx.get_dialog(ctx, actor)
    if isinstance(response_phrases, dict):
        if dialog["seen"]:
            response = random.choice(response_phrases["last"]).strip()
        else:
            response = random.choice(response_phrases["first"]).strip()
    else:
        response = random.choice(response_phrases).strip()

    # TODO: somehow response sometimes is dict
    if type(response) == dict:
        if dialog["seen"]:
            response = random.choice(response["last"]).strip()
        else:
            response = random.choice(response["first"]).strip()
    return response


def random_respond_with_question_asking(ctx: Context, actor: Actor, intention: str):
    utt = int_ctx.get_last_human_utterance(ctx, actor)
    response = random_respond(ctx, actor, intention)
    if "you" in utt:
        you = "you"
    else:
        you = "yours"
    response = f"{response}. And {you}?"
    return response


def what_time_respond(ctx: Context, actor: Actor, intention: str):
    time = datetime.utcnow()
    response = f"It is {time.hour} hours and {time.minute} minutes by U. T. C. What a time to be alive!"
    return response


def what_is_current_dialog_id_respond(ctx: Context, actor: Actor, intention: str):
    dialog = int_ctx.get_dialog(ctx, actor)
    dialog_id = dialog.get("dialog_id", "unknown")
    response = f"Dialog id is: {dialog_id}"
    return response


def get_respond_funcs():
    return {
        "exit": random_respond,
        "repeat": repeat_respond,
        "where_are_you_from": where_are_you_from_respond,
        "get_dialog_id": what_is_current_dialog_id_respond,
        "who_made_you": random_respond,
        "what_is_your_name": random_respond,
        "what_is_your_job": random_respond,
        "what_can_you_do": random_respond,
        "what_time": what_time_respond,
        "dont_understand": random_respond,
        "choose_topic": random_respond,
        "cant_do": random_respond,
        "tell_me_a_story": random_respond,
        "track_object": track_object_respond,
        "turn_around": turn_around_respond,
        "move_forward": move_forward_respond,
        "move_backward": move_backward_respond,   
    }


def get_human_utterances(ctx: Context, actor: Actor) -> list:
    return {} if ctx.validation else ctx.misc["agent"]["dialog"]["human_utterances"]

################# CUSTOM FOR ROBOT

def track_object_respond(ctx: Context, actor: Actor, intention: str):
    utt = int_ctx.get_last_human_utterance(ctx, actor)
    entities = get_entities(utt, only_named=False, with_labels=False)
    if len(entities) == 1:
        response = f"track_object_{entities[0]}"
    else:
        response = "track_object_unknown"
    return response

def turn_around_respond(ctx: Context, actor: Actor, intention: str):
    utt = int_ctx.get_last_human_utterance(ctx, actor)
    if re.search(r"clock-?wise", utt["text"]):
        response = "turn_clockwise"
    else:
        response = "turn_counterclockwise"
    return response

def move_forward_respond(ctx: Context, actor: Actor, intention: str):
    utt = int_ctx.get_last_human_utterance(ctx, actor)
    dist = re.findall(r"[0-9]+", utt["text"])
    if len(dist) == 1:
        response = f"move_forward_{dist[0]}"
    else:
        response = f"move_forward"
        
    return response

def move_backward_respond(ctx: Context, actor: Actor, intention: str):
    utt = int_ctx.get_last_human_utterance(ctx, actor)
    dist = re.findall(r"[0-9]+", utt["text"])
    if len(dist) == 1:
        response = f"move_backward_{dist[0]}"
    else:
        response = f"move_backward"
    return response