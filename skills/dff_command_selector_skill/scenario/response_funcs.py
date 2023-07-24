#!/usr/bin/env python
import logging
import re
from os import getenv

import common.dff.integration.context as int_ctx
from common.robot import check_if_valid_robot_command
from common.utils import get_entities
from df_engine.core import Actor, Context


LANGUAGE = getenv("LANGUAGE", "EN")
ROS_FSM_SERVER = getenv("ROS_FSM_SERVER")

logging.basicConfig(format="%(asctime)s - %(pathname)s - %(lineno)d - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)


def get_respond_funcs():
    return {
        "track_object": track_object_respond,
        "turn_around": turn_around_respond,
        "move_forward": move_forward_respond,
        "move_backward": move_backward_respond,
        "open_door": open_door_respond,
        "move_to_point": move_to_point_respond,
    }


def get_human_utterances(ctx: Context, actor: Actor) -> list:
    return {} if ctx.validation else ctx.misc["agent"]["dialog"]["human_utterances"]


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

    if check_if_valid_robot_command(command, ROS_FSM_SERVER, dialog_id=int_ctx.get_dialog_id(ctx, actor)):
        return response, 1.0, {}, {}, {"command_to_perform": command}
    else:
        return ""


def turn_around_respond(ctx: Context, actor: Actor, intention: str):
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

    if check_if_valid_robot_command(command, ROS_FSM_SERVER, dialog_id=int_ctx.get_dialog_id(ctx, actor)):
        return response, 1.0, {}, {}, {"command_to_perform": command}
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
            response = "Двигаюсь вперед."
        else:
            response = "Moving forward."

    if check_if_valid_robot_command(command, ROS_FSM_SERVER, dialog_id=int_ctx.get_dialog_id(ctx, actor)):
        return response, 1.0, {}, {}, {"command_to_perform": command}
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
            response = "Двигаюсь назад."
        else:
            response = "Moving backward."

    if check_if_valid_robot_command(command, ROS_FSM_SERVER, dialog_id=int_ctx.get_dialog_id(ctx, actor)):
        return response, 1.0, {}, {}, {"command_to_perform": command}
    else:
        return ""


def open_door_respond(ctx: Context, actor: Actor, intention: str):
    command = "open_door"
    if LANGUAGE == "RU":
        response = "Открываю дверь"
    else:
        response = "Opening the door."

    if check_if_valid_robot_command(command, ROS_FSM_SERVER, dialog_id=int_ctx.get_dialog_id(ctx, actor)):
        return response, 1.0, {}, {}, {"command_to_perform": command}
    else:
        return ""


# covers coords like "5,35", "5, 35", "5 35"
COMPILED_COORDS_PATTERN = re.compile(r"[-][0-9]+[ ,]+[-][0-9]+", re.IGNORECASE)


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
            response = "I did not get a target point. Please repeat the command."

    if check_if_valid_robot_command(command, ROS_FSM_SERVER, dialog_id=int_ctx.get_dialog_id(ctx, actor)):
        return response, 1.0, {}, {}, {"command_to_perform": command}
    else:
        return ""
