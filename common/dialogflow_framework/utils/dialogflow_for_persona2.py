#!/usr/bin/env python

import logging
import os

import sentry_sdk
from sentry_sdk.integrations.logging import ignore_logger

import common.dialogflow_framework.stdm.cached_functions as cached_functions
from common.constants import CAN_NOT_CONTINUE, CAN_CONTINUE_SCENARIO

ignore_logger("root")

sentry_sdk.init(os.getenv("SENTRY_DSN"))

logger = logging.getLogger(__name__)


def load_into_dialogflow(dialogflow, human_utter_index, dialog, state, entities, used_links, disliked_skills):
    cached_functions.clear_cache()
    dialogflow.reset()
    dialogflow_state = state.get("dialogflow_state")
    previous_human_utter_index = state.get("previous_human_utter_index", -1)
    interrupted_flag = (human_utter_index - previous_human_utter_index) != 1
    if dialogflow_state and not interrupted_flag:
        logger.info(f"DESERIALIZE WAS CALLED, CONTENT = {dialogflow_state}")
        dialogflow.deserialize(dialogflow_state)
    else:
        logger.info(f"DESERIALIZE WASN'T CALLED, CONTENT = {dialogflow_state}, INTERRUPTED_FLAG = {interrupted_flag}")
    agent = {
        "previous_human_utter_index": previous_human_utter_index,
        "human_utter_index": human_utter_index,
        "dialog": dialog,
        "entities": entities,
        "shared_memory": state.get("shared_memory", {}),
        "response": {},
        "cache": {},
        "history": state.get("history", {}),
        "used_links": used_links,
        "disliked_skills": disliked_skills,
    }
    dialogflow.controller().vars()["agent"] = agent


def get_dialog_state(dialogflow):
    agent = dialogflow.controller().vars()["agent"]
    human_utter_index = agent["human_utter_index"]
    history = agent["history"]
    used_links = agent["used_links"]
    disliked_skills = agent["disliked_skills"]
    history[str(human_utter_index)] = dialogflow.controller().vars()["__system_state__"]
    state = {
        "shared_memory": agent["shared_memory"],
        "previous_human_utter_index": human_utter_index,
        "history": history,
    }
    del dialogflow.controller().vars()["agent"]
    state["dialogflow_state"] = dialogflow.serialize()
    logger.debug(f"state={state}")
    return state, used_links, disliked_skills


def run_turn(dialogflow, text):
    dialogflow.user_turn(text)
    text = dialogflow.system_turn()
    confidence = dialogflow.controller().vars()["agent"]["response"].get("confidence", 0.85)
    can_continue = CAN_CONTINUE_SCENARIO if confidence else CAN_NOT_CONTINUE
    can_continue = dialogflow.controller().vars()["agent"]["response"].get("can_continue", can_continue)
    return text, confidence, can_continue
