#!/usr/bin/env python

import logging
import os
import json
from typing import List, Any

import sentry_sdk
from sentry_sdk.integrations.logging import ignore_logger

from common.constants import CAN_NOT_CONTINUE, CAN_CONTINUE_SCENARIO

from dff.script import Context, Actor
from pydantic import BaseModel, Field, Extra, root_validator

ignore_logger("root")

sentry_sdk.init(os.getenv("SENTRY_DSN"))
SERVICE_NAME = os.getenv("SERVICE_NAME")

logger = logging.getLogger(__name__)


class ExtraIgnoreModel(BaseModel):
    class Config:
        extra = Extra.ignore


class HumanAttr(ExtraIgnoreModel):
    dff_shared_state: dict
    used_links: dict
    age_group: str
    disliked_skills: list


class HypeAttr(ExtraIgnoreModel):
    can_continue: str

    @root_validator(pre=True)
    def calculate_can_continue(cls, values):
        confidence = values["response"].get("confidence", 0.85)
        can_continue = CAN_CONTINUE_SCENARIO if confidence else CAN_NOT_CONTINUE
        values["can_continue"] = values["response"].get("can_continue", can_continue)
        return values


class State(ExtraIgnoreModel):
    context: dict
    previous_human_utter_index: int = -1
    current_turn_dff_suspended: bool = False
    history: dict = Field(default_factory=dict)
    shared_memory: dict = Field(default_factory=dict)

    @root_validator(pre=True)
    def shift_state_history(cls, values):
        values["previous_human_utter_index"] = values["human_utter_index"]
        values["history"][str(values["human_utter_index"])] = list(values["context"].labels.values())[-1]
        return values

    @root_validator(pre=True)
    def validate_context(cls, values):
        context = values["context"]
        context.clear(2, ["requests", "responses", "labels"])
        del context.misc["agent"]
        values["context"] = json.loads(context.json())
        return values


class Agent(ExtraIgnoreModel):
    previous_human_utter_index: int = -1
    human_utter_index: int
    dialog: Any
    entities: dict = Field(default_factory=dict)
    shared_memory: dict = Field(default_factory=dict)
    current_turn_dff_suspended: bool = False
    previous_turn_dff_suspended: bool = False
    response: dict = Field(default_factory=dict)
    dff_shared_state: dict = Field(default_factory=dict)
    cache: dict = Field(default_factory=dict)
    history: dict = Field(default_factory=dict)
    used_links: dict = Field(default_factory=dict)
    age_group: str = ""
    disliked_skills: list = Field(default_factory=list)
    clarification_request_flag: bool = False

    @root_validator(pre=True)
    def get_state_props(cls, values):
        state = values.get("state", {})
        values = values | state
        return values


def load_ctxs(requested_data) -> List[Context]:
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
    ):
        ctx = Context.cast(state.get("context", {}))
        agent = Agent(**locals())
        ctx.misc["agent"] = agent.dict()
        ctxs += [ctx]
    return ctxs


def get_response(ctx: Context, actor: Actor):
    agent = ctx.misc["agent"]
    response_parts = agent.get("response_parts", [])
    confidence = agent["response"].get("confidence", 0.85)
    state = State(context=ctx, **agent).dict()
    human_attr = HumanAttr.parse_obj(agent).dict() | {f"{SERVICE_NAME}_state": state}
    hype_attr = HypeAttr.parse_obj(agent).dict() | ({"response_parts": response_parts} if response_parts else {})
    response = ctx.last_response
    messages = getattr(response, "messages", None)
    if messages is not None:
        responses = []
        for message in messages:
            reply = message.text
            misc = message.misc
            conf = misc.get("confidence") or confidence
            h_a = human_attr | misc.get("human_attr")
            attr = hype_attr | misc.get("hype_attr")
            responses += [(reply, conf, h_a, misc.get("bot_attr"), attr)]
        return list(zip(*responses))
    else:
        return (response.text, confidence, human_attr, {}, hype_attr)
