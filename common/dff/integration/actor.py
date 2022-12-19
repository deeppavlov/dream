#!/usr/bin/env python

import logging
import os
import json

import sentry_sdk
from sentry_sdk.integrations.logging import ignore_logger

from common.constants import CAN_NOT_CONTINUE, CAN_CONTINUE_SCENARIO

from df_engine.core import Context, Actor

ignore_logger("root")

sentry_sdk.init(os.getenv("SENTRY_DSN"))
SERVICE_NAME = os.getenv("SERVICE_NAME")

logger = logging.getLogger(__name__)


def load_ctxs(requested_data):
    dialog_batch = requested_data.get("dialog_batch", [])
    human_utter_index_batch = requested_data.get("human_utter_index_batch", [0] * len(dialog_batch))
    state_batch = requested_data.get(f"{SERVICE_NAME}_state_batch", [{}] * len(dialog_batch))
    dff_shared_state_batch = requested_data.get("dff_shared_state_batch", [{}] * len(dialog_batch))
    entities_batch = requested_data.get("entities_batch", [{}] * len(dialog_batch))
    used_links_batch = requested_data.get("used_links_batch", [{}] * len(dialog_batch))
    age_group_batch = requested_data.get("age_group_batch", [""] * len(dialog_batch))
    disliked_skills_batch = requested_data.get("disliked_skills_batch", [{}] * len(dialog_batch))
    clarification_request_flag_batch = requested_data.get(
        "clarification_request_flag_batch",
        [False] * len(dialog_batch),
    )
    dialog_id_batch = requested_data.get("dialog_id_batch", [0] * len(dialog_batch))

    ctxs = []
    for (
        human_utter_index,
        dialog,
        state,
        dff_shared_state,
        entities,
        used_links,
        age_group,
        disliked_skills,
        clarification_request_flag,
        dialog_id,
    ) in zip(
        human_utter_index_batch,
        dialog_batch,
        state_batch,
        dff_shared_state_batch,
        entities_batch,
        used_links_batch,
        age_group_batch,
        disliked_skills_batch,
        clarification_request_flag_batch,
        dialog_id_batch,
    ):
        ctx = get_ctx(
            human_utter_index,
            dialog,
            state,
            dff_shared_state,
            entities,
            used_links,
            age_group,
            disliked_skills,
            clarification_request_flag,
            dialog_id,
        )
        ctxs += [ctx]
    return ctxs


def get_ctx(
    human_utter_index,
    dialog,
    state,
    dff_shared_state,
    entities,
    used_links,
    age_group,
    disliked_skills,
    clarification_request_flag,
    dialog_id,
):
    context = state.get("context", {})
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
        "dialog_id": dialog_id,
    }
    ctx = Context.cast(context)
    ctx.misc["agent"] = agent
    ctx.add_request(dialog["human_utterances"][-1]["text"])
    return ctx


def get_response(ctx: Context, actor: Actor, *args, **kwargs):
    agent = ctx.misc["agent"]
    human_utter_index = agent["human_utter_index"]
    dff_shared_state = agent["dff_shared_state"]
    history = agent["history"]
    used_links = agent["used_links"]
    age_group = agent["age_group"]
    disliked_skills = agent["disliked_skills"]
    current_turn_dff_suspended = agent["current_turn_dff_suspended"]
    response_parts = agent.get("response_parts", [])
    history[str(human_utter_index)] = list(ctx.labels.values())[-1]
    state = {
        "shared_memory": agent["shared_memory"],
        "previous_human_utter_index": human_utter_index,
        "history": history,
        "current_turn_dff_suspended": current_turn_dff_suspended,
    }
    confidence = ctx.misc["agent"]["response"].get("confidence", 0.85)
    can_continue = CAN_CONTINUE_SCENARIO if confidence else CAN_NOT_CONTINUE
    can_continue = ctx.misc["agent"]["response"].get("can_continue", can_continue)
    ctx.clear(2, ["requests", "responses", "labels"])
    del ctx.misc["agent"]
    state["context"] = json.loads(ctx.json())

    human_attr = {
        f"{SERVICE_NAME}_state": state,
        "dff_shared_state": dff_shared_state,
        "used_links": used_links,
        "age_group": age_group,
        "disliked_skills": disliked_skills,
    }
    hype_attr = {"can_continue": can_continue}
    if response_parts:
        hype_attr["response_parts"] = response_parts
    response = ctx.last_response
    if isinstance(response, list):
        responses = []
        for reply, conf, h_a, b_a, attr in response:
            conf = conf if conf else confidence
            h_a = human_attr | h_a
            attr = hype_attr | attr
            responses += [(reply, conf, h_a, b_a, attr)]
        return list(zip(*responses))
    else:
        return (response, confidence, human_attr, {}, hype_attr)
