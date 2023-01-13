#!/usr/bin/env python

import json
import random
import common.dff.integration.context as int_ctx
from datetime import datetime
from df_engine.core import Actor, Context

INTENT_RESPONSES_PATH = "scenario/data/intent_response_phrases.json"


with open(INTENT_RESPONSES_PATH, "r") as fp:
    RESPONSES = json.load(fp)


def default_response(ctx: Context, actor: Actor, intention: str):
    response_phrases = RESPONSES[intention]
    response = random.choice(response_phrases).strip()

    return response


def get_response_funcs():
    return {
        "goto": default_response,
        "goto_user": default_response,
        "follow_me": default_response,
        "stop": default_response,
        "destroy_block": default_response,
        "place_block": default_response,
        "destroy_and_grab_block": default_response,
        "look_at_user": default_response,
        "build_house": default_response,
        "recreate": default_response,
        "start_building": default_response,
        "finish_building": default_response
    }


def get_human_utterances(ctx: Context, actor: Actor) -> list:
    return {} if ctx.validation else ctx.misc["agent"]["dialog"]["human_utterances"]
