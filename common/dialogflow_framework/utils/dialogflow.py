#!/usr/bin/env python

import logging
import os

import sentry_sdk
from sentry_sdk.integrations.logging import ignore_logger

from common.constants import CAN_NOT_CONTINUE, CAN_CONTINUE_SCENARIO

ignore_logger("root")

sentry_sdk.init(os.getenv("SENTRY_DSN"))

logger = logging.getLogger(__name__)


def load_into_dialogflow(
    human_utter_index,
    dialog,
    state,
    dff_shared_state,
    entities,
    used_links,
    age_group,
    disliked_skills,
    clarification_request_flag,
):
    previous_human_utter_index = state.get("previous_human_utter_index", -1)
    current_turn_dff_suspended = state.get("current_turn_dff_suspended", False)

    agent = {
        "previous_human_utter_index": previous_human_utter_index,
        "human_utter_index": human_utter_index,
        "dialog": dialog,
        "entities": entities,
        "shared_memory": state.get("shared_memory", {}),
        "previous_turn_dff_suspended": current_turn_dff_suspended,
        "current_turn_dff_suspended": False,
        "response": {},
        "dff_shared_state": dff_shared_state,
        "cache": {},
        "history": state.get("history", {}),
        "used_links": used_links,
        "age_group": age_group,
        "disliked_skills": disliked_skills,
        "clarification_request_flag": clarification_request_flag,
    }
    return agent


def get_dialog_state(vars):
    agent = vars["agent"]
    human_utter_index = agent["human_utter_index"]
    dff_shared_state = agent["dff_shared_state"]
    history = agent["history"]
    used_links = agent["used_links"]
    age_group = agent["age_group"]
    disliked_skills = agent["disliked_skills"]
    current_turn_dff_suspended = agent["current_turn_dff_suspended"]
    response_parts = agent.get("response_parts", [])
    state = {
        "shared_memory": agent["shared_memory"],
        "previous_human_utter_index": human_utter_index,
        "history": history,
        "current_turn_dff_suspended": current_turn_dff_suspended,
    }
    logger.debug(f"state={state}")
    return state, dff_shared_state, used_links, age_group, disliked_skills, response_parts


def run_turn(dialogflow, text):
    dialogflow.user_turn(text)
    text = dialogflow.system_turn()
    confidence = dialogflow.controller().vars()["agent"]["response"].get("confidence", 0.85)
    can_continue = CAN_CONTINUE_SCENARIO if confidence else CAN_NOT_CONTINUE
    can_continue = dialogflow.controller().vars()["agent"]["response"].get("can_continue", can_continue)
    return text, confidence, can_continue
