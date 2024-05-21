#!/usr/bin/env python
import logging
import re
from os import getenv

import common.dff.integration.context as int_ctx
from common.robot import check_if_valid_robot_command
from common.utils import get_entities
from df_engine.core import Actor, Context


LANGUAGE = getenv("LANGUAGE", "EN")
ROS_FLASK_SERVER = getenv("ROS_FLASK_SERVER")

logging.basicConfig(format="%(asctime)s - %(pathname)s - %(lineno)d - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)


def get_respond_funcs():
    return {
        "test_command": test_command_respond,
        "track_object": track_object_respond,
        "turn_around": turn_around_respond,
        "move_forward": move_forward_respond,
        "move_backward": move_backward_respond,
        "open_door": open_door_respond,
        "move_to_point": move_to_point_respond,
        "approach": approach_respond,
        "pick_up": pick_up_respond,
        "place": place_respond, 
        "say": say_respond,
        "sit_down": sit_down_respond,
        "stand_up": stand_up_respond,
        "stop": stop_respond,
        "turn_right": turn_right_respond,
        "turn_left": turn_left_respond,
        "status": status_respond,
        "enable_autopilot": enable_autopilot_respond,
        "disable_autopilot": disable_autopilot_respond,
    }


def get_human_utterances(ctx: Context, actor: Actor) -> list:
    return {} if ctx.validation else ctx.misc["agent"]["dialog"]["human_utterances"]


def test_command_respond(ctx: Context, actor: Actor):
    command = "test_command"
    response = "Success"

    return response, 1.0, {}, {}, {"command_to_perform": command}
    

def track_object_respond(ctx: Context, actor: Actor):
    utt = int_ctx.get_last_human_utterance(ctx, actor)
    entities = re.findall(r"\b(\w+)\b", utt["text"])
    if len(entities) == 1:
        command = f"track_object_{entities[0]}"
        response = f"Следую за объектом: {entities[0]}." if LANGUAGE == "RU" else f"Tracking object: {entities[0]}."
    else:
        command = "track_object_unknown"
        if LANGUAGE == "RU":
            response = "Не могу извлечь объект для отслеживания. Повторите команду."
        else:
            response = "I did not get tracked object. Please repeat the command."

    return response, 1.0, {}, {}, {"command_to_perform": command}
    

def turn_around_respond(ctx: Context, actor: Actor):
    utt = int_ctx.get_last_human_utterance(ctx, actor)
    degree = re.findall(r"[0-9]+", utt["text"])
    if "против" in utt["text"] or re.search(r"counter[- ]?clock-?wise", utt["text"]):
        if len(degree) == 1:
            command = f"turn_counterclockwise_{degree[0]}"
            if LANGUAGE == "RU":
                response = f"Поворачиваюсь против часовой стрелки на {degree[0]} градусов."
            else:
                response = f"Turning around counterclockwise by {degree[0]} degrees."
        else:
            command = "turn_counterclockwise"
            if LANGUAGE == "RU":
                response = "Поворачиваюсь против часовой стрелки."
            else:
                response = "Turning around counterclockwise."
    else:
        if len(degree) == 1:
            command = f"turn_clockwise_{degree[0]}"
            if LANGUAGE == "RU":
                response = f"Поворачиваюсь по часовой стрелке на {degree[0]} градусов."
            else:
                response = f"Turning around clockwise by {degree[0]} degrees."
        else:
            command = "turn_clockwise"
            if LANGUAGE == "RU":
                response = "Поворачиваюсь по часовой стрелке."
            else:
                response = "Turning around clockwise."

    return response, 1.0, {}, {}, {"command_to_perform": command}
    

def approach_respond(ctx: Context, actor: Actor):
    utt = int_ctx.get_last_human_utterance(ctx, actor)
    target = re.findall(r"к (\w+)|иди (\w+)", utt["text"])
    target = target[0][0] if target[0][0] else target[0][1]
    if target:
        command = f"approach_{target}"
        if LANGUAGE == "RU":
            response = f"Подхожу к {target}."
        else:
            response = f"Approaching {target}."
    else:
        command = "approach"
        if LANGUAGE == "RU":
            response = "Подхожу."
        else:
            response = "Approaching."

    return response, 1.0, {}, {}, {"command_to_perform": command}


def pick_up_respond(ctx: Context, actor: Actor):
    utt = int_ctx.get_last_human_utterance(ctx, actor)
    # Extracting entities to identify what object to pick up.
    entities = get_entities(utt, only_named=False, with_labels=False, return_lemmas=True)
    if entities:
        command = f"pick_up_{entities[0]}"
        response = f"Picking up {entities[0]}." if LANGUAGE == "EN" else f"Беру {entities[0]}."
    else:
        command = "pick_up_unknown"
        response = "I did not get which item to pick up. Please repeat the command." if LANGUAGE == "EN" else "Не понял, что взять. Пожалуйста, повторите команду."
        
    # Since command validation is not required, we proceed directly to action.
    return response, 1.0, {}, {}, {"command_to_perform": command}



def place_respond(ctx: Context, actor: Actor):
    utt = int_ctx.get_last_human_utterance(ctx, actor)
    # Extract the object and location using a regex pattern or predefined logic based on your intent phrases
    object_match = re.search(r"(эту книгу|те журналы|эту вещь|это|ту книгу|те книжки|книгу|стул|эту коробку)", utt["text"])
    location_match = re.search(r"(на стол|в угол|здесь|там|на полку|у стены|на пороге)", utt["text"])

    if object_match and location_match:
        object_to_place = object_match.group(0)
        location_to_place = location_match.group(0)
        command = f"place_{object_to_place}_at_{location_to_place}"
        response = f"Placing {object_to_place} at {location_to_place}." if LANGUAGE == "EN" else f"Ставлю {object_to_place} {location_to_place}."
    else:
        command = "place_unknown"
        response = "Please specify what and where to place." if LANGUAGE == "EN" else "Пожалуйста, уточните, что и куда поставить."

    return response, 1.0, {}, {}, {"command_to_perform": command}


def say_respond(ctx: Context, actor: Actor):
    utt = int_ctx.get_last_human_utterance(ctx, actor)
    text = utt["text"]
    
    # Regular expressions to extract specific requests from the text
    # Example: "скажи что-нибудь" or "можешь сказать, как дела?"
    anything_pattern = re.compile(r"что-нибудь", re.IGNORECASE)
    repeat_words_pattern = re.compile(r"повтори (мои слова|за мной)", re.IGNORECASE)
    
    response = ""
    if anything_pattern.search(text) or "скажи" in text:
        response = "Конечно, вот мое сообщение." if LANGUAGE == "RU" else "Sure, here's my message."
    elif repeat_words_pattern.search(text):
        words_to_repeat = re.findall(r"повтори (.*)", text)
        response = words_to_repeat[0] if words_to_repeat else "Что именно повторить?"

    return response, 1.0 if response else 0.0, {}, {}, {"command_to_perform": "say_something"}

def sit_down_respond(ctx: Context, actor: Actor):
    command = "sit_down"
    if LANGUAGE == "RU":
        response = "Сажусь."
    else:
        response = "Sitting down."

    return response, 1.0, {}, {}, {"command_to_perform": command}


def stand_up_respond(ctx: Context, actor: Actor):
    command = "stand_up"
    if LANGUAGE == "RU":
        response = "Встаю."
    else:
        response = "Standing up."

    return response, 1.0, {}, {}, {"command_to_perform": command}


def  stop_respond(ctx: Context, actor: Actor):
    command = "stop"
    if LANGUAGE == "RU":
        response = "Остановка выполнена."
    else:
        response = "Stop executed."

    return response, 1.0, {}, {}, {"command_to_perform": command}



def move_forward_respond(ctx: Context, actor: Actor):
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
            response = "Двигаюсь вперед."
        else:
            response = "Moving forward."

    return response, 1.0, {}, {}, {"command_to_perform": command}
    

def move_backward_respond(ctx: Context, actor: Actor):
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
            response = "Двигаюсь назад."
        else:
            response = "Moving backward."

    return response, 1.0, {}, {}, {"command_to_perform": command}
    

def open_door_respond(ctx: Context, actor: Actor):
    command = "open_door"
    if LANGUAGE == "RU":
        response = "Открываю дверь"
    else:
        response = "Opening the door."

    return response, 1.0, {}, {}, {"command_to_perform": command}
    
def turn_right_respond(ctx: Context, actor: Actor):
    command = "turn_right"
    response = "command"
    return response, 1.0, {}, {}, {"command_to_perform": command}

def turn_left_respond(ctx: Context, actor: Actor):
    command = "turn_left"
    response = "command"
    return response, 1.0, {}, {}, {"command_to_perform": command}

def status_respond(ctx: Context, actor: Actor):
    command = "status"
    response = "command"
    return response, 1.0, {}, {}, {"command_to_perform": command}

def enable_autopilot_respond(ctx: Context, actor: Actor):
    command = "enable_autopilot"
    response = "command"
    return response, 1.0, {}, {}, {"command_to_perform": command}

def disable_autopilot_respond(ctx: Context, actor: Actor):
    command = "disable_autopilot"
    response = "command"
    return response, 1.0, {}, {}, {"command_to_perform": command}


# covers coords like "5,35", "5, 35", "5 35"
COMPILED_COORDS_PATTERN = re.compile(r"[-][0-9]+[ ,]+[-][0-9]+", re.IGNORECASE)


def move_to_point_respond(ctx: Context, actor: Actor):
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
            response = "I did not get a target point. Please repeat the command."

    return response, 1.0, {}, {}, {"command_to_perform": command}
    