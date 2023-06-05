#!/usr/bin/env python
import logging
import re
from os import getenv

import common.dff.integration.context as int_ctx
from common.robot import check_if_valid_robot_command
from df_engine.core import Actor, Context


LANGUAGE = getenv("LANGUAGE", "EN")
ROS_FLASK_SERVER = getenv("ROS_FLASK_SERVER")

logging.basicConfig(format="%(asctime)s - %(pathname)s - %(lineno)d - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)


def get_respond_funcs():
    return {
        "move_forward": move_forward_respond,
        "move_backward": move_backward_respond,
    }


def get_human_utterances(ctx: Context, actor: Actor) -> list:
    return {} if ctx.validation else ctx.misc["agent"]["dialog"]["human_utterances"]


def move_forward_respond(ctx: Context, actor: Actor, intention: str):
    utt = int_ctx.get_last_human_utterance(ctx, actor)
    dist = re.findall(r"[0-9]+", utt["text"])
    if len(dist) == 1:
        command = f"move_forward_{dist[0]}"
        response = f"Moving forward by {dist[0]} units."
    else:
        command = "move_forward"
        response = "Moving forward."

    if check_if_valid_robot_command(command, ROS_FLASK_SERVER, dialog_id=int_ctx.get_dialog_id(ctx, actor)):
        return response, 1.0, {}, {}, {"command_to_perform": command}
    else:
        return ""


def move_backward_respond(ctx: Context, actor: Actor, intention: str):
    utt = int_ctx.get_last_human_utterance(ctx, actor)
    dist = re.findall(r"[0-9]+", utt["text"])
    if len(dist) == 1:
        command = f"move_backward_{dist[0]}"
        response = f"Moving backward by {dist[0]} units."
    else:
        command = "move_backward"
        response = "Moving backward."

    if check_if_valid_robot_command(command, ROS_FLASK_SERVER, dialog_id=int_ctx.get_dialog_id(ctx, actor)):
        return response, 1.0, {}, {}, {"command_to_perform": command}
    else:
        return ""
