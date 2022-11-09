#!/usr/bin/env python
import logging
import json
import random
import re
from datetime import datetime
from os import getenv
import requests
import json

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
        "open_door": open_door_respond,
        "move_to_point": move_to_point_respond
    }


def get_human_utterances(ctx: Context, actor: Actor) -> list:
    return {} if ctx.validation else ctx.misc["agent"]["dialog"]["human_utterances"]


def check_if_valid_robot_command(command):
    ROS_FSM_SERVER = "http://172.17.0.1:5000"
    ROS_FSM_INTENT_ENDPOINT = f"{ROS_FSM_SERVER}/upload_response"
    logger.info(f"Sending to robot:\n{command}")

    requests.post(ROS_FSM_INTENT_ENDPOINT, data=json.dumps({"text": command}))


def track_object_respond(ctx: Context, actor: Actor, intention: str):
    utt = int_ctx.get_last_human_utterance(ctx, actor)
    entities = get_entities(utt, only_named=False, with_labels=False, return_lemmas=True)
    if len(entities) == 1:
        command = f"track_object_{entities[0]}"
        response = f"Следую за объектом: {entities[0]}." if LANGUAGE == "RU" else f"Tracking object: {entities[0]}."
    else:
        command = "track_object_unknown"
        if LANGUAGE == "RU":
            response = "Не могу извлечь объект для отслеживания. Повторите команду."
        else:
            response = "I did not get tracked object. Please repeat the command."

    if check_if_valid_robot_command(command):
        return response
    else:
        return ""


def turn_around_respond(ctx: Context, actor: Actor, intention: str):
    utt = int_ctx.get_last_human_utterance(ctx, actor)
    degree = re.findall(r"[0-9]+", utt["text"])
    if "против" in utt["text"]:
        command = f"turn_counterclockwise_{degree[0]}"
        if len(degree) == 1:
            if LANGUAGE == "RU":
                response = f"Поворачиваюсь против часовой стрелки на {degree[0]} градусов."
            else:
                response = f"Turning around counterclockwise by {degree[0]} degrees."
        else:
            if LANGUAGE == "RU":
                response = f"Поворачиваюсь против часовой стрелки."
            else:
                response = f"Turning around counterclockwise."
    else:
        command = f"turn_clockwise_{degree[0]}"
        if len(degree) == 1:
            if LANGUAGE == "RU":
                response = f"Поворачиваюсь по часовой стрелке на {degree[0]} градусов."
            else:
                response = f"Turning around clockwise by {degree[0]} degrees."
        else:
            if LANGUAGE == "RU":
                response = f"Поворачиваюсь по часовой стрелке."
            else:
                response = f"Turning around clockwise."

    if check_if_valid_robot_command(command):
        return response
    else:
        return ""


def move_forward_respond(ctx: Context, actor: Actor, intention: str):
    utt = int_ctx.get_last_human_utterance(ctx, actor)
    dist = re.findall(r"[0-9]+", utt["text"])
    if len(dist) == 1:
        command = f"move_forward_{dist[0]}"
        if LANGUAGE == "RU":
            response = f"Двигаюсь вперед на {dist[0]} метров."
        else:
            response = f"Moving forward by {dist[0]} meters."
    else:
        command = "move_forward"
        if LANGUAGE == "RU":
            response = f"Двигаюсь вперед."
        else:
            response = f"Moving forward."

    if check_if_valid_robot_command(command):
        return response
    else:
        return ""


def move_backward_respond(ctx: Context, actor: Actor, intention: str):
    utt = int_ctx.get_last_human_utterance(ctx, actor)
    dist = re.findall(r"[0-9]+", utt["text"])
    if len(dist) == 1:
        command = f"move_backward_{dist[0]}"
        if LANGUAGE == "RU":
            response = f"Двигаюсь назад на {dist[0]} метров."
        else:
            response = f"Moving backward by {dist[0]} meters."
    else:
        command = "move_backward"
        if LANGUAGE == "RU":
            response = f"Двигаюсь назад."
        else:
            response = f"Moving backward."

    if check_if_valid_robot_command(command):
        return response
    else:
        return ""


def open_door_respond(ctx: Context, actor: Actor, intention: str):
    command = "open_door"
    if LANGUAGE == "RU":
        response = f"Открываю дверь"
    else:
        response = f"Opening the door."

    if check_if_valid_robot_command(command):
        return response
    else:
        return ""


# covers coords like "5,35", "5, 35", "5 35"
COMPILED_COORDS_PATTERN = re.compile(r"[0-9]+[ ,]+[0-9]+", re.IGNORECASE)


def move_to_point_respond(ctx: Context, actor: Actor, intention: str):
    utt = int_ctx.get_last_human_utterance(ctx, actor)
    entities = get_entities(utt, only_named=False, with_labels=False, return_lemmas=True)
    coords = COMPILED_COORDS_PATTERN.search(utt["text"])
    if len(entities) == 1:
        command = f"move_to_point_{entities[0]}"
        response = f"Двигаюсь к объекту: {entities[0]}." if LANGUAGE == "RU" else f"Moving to object: {entities[0]}."
    elif coords:
        command = f"move_to_point_{coords[0]}"
        response = f"Двигаюсь в точку: {coords[0]}." if LANGUAGE == "RU" else f"Moving to point: {coords[0]}."
    else:
        command = "move_to_point_unknown"
        if LANGUAGE == "RU":
            response = "Не могу извлечь объект для цели. Повторите команду."
        else:
            response = "I did not get target object. Please repeat the command."

    if check_if_valid_robot_command(command):
        return response
    else:
        return ""
