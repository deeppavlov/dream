#!/usr/bin/env python

import logging
import os
from typing import List, Any

import sentry_sdk
from sentry_sdk.integrations.logging import ignore_logger
from dff.script import Context, MultiMessage
from dff.pipeline import Pipeline
from pydantic import BaseModel, Field, Extra, root_validator

from common.constants import CAN_NOT_CONTINUE, CAN_CONTINUE_SCENARIO
from common.dff_api_v1.integration.context import get_last_human_utterance
from common.dff_api_v1.integration.message import DreamMessage


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
    context: Context
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
        agent = Agent(
            human_utter_index=human_utter_index,
            dialog=dialog,
            state=state,
            dff_shared_state=dff_shared_state,
            entities=entities,
            used_links=used_links,
            age_group=age_group,
            disliked_skills=disliked_skills,
            clarification_request_flag=clarification_request_flag,
        )
        ctx.misc["agent"] = agent.dict()
        ctxs += [ctx]
    return ctxs


def get_response(ctx: Context, _):
    agent = ctx.misc["agent"]
    response_parts = agent.get("response_parts", [])
    confidence = agent["response"].get("confidence", 0.85)
    state = State(context=ctx, **agent).dict(exclude_none=True)
    human_attr = HumanAttr.parse_obj(agent).dict() | {f"{SERVICE_NAME}_state": state}
    hype_attr = HypeAttr.parse_obj(agent).dict() | ({"response_parts": response_parts} if response_parts else {})
    response = ctx.last_response
    if isinstance(response, MultiMessage):
        responses = []
        message: dict
        for message in response.messages:
            reply = message.text or ""
            conf = message.confidence or confidence
            h_a = human_attr | (message.human_attr or {})
            attr = hype_attr | (message.hype_attr or {})
            b_a = message.bot_attr or {}
            responses += [(reply, conf, h_a, b_a, attr)]
        return list(zip(*responses))
    else:
        return (response.text, confidence, human_attr, {}, hype_attr)


def run_dff(ctx: Context, pipeline: Pipeline):
    last_request = get_last_human_utterance(ctx, pipeline.actor)["text"]
    pipeline.context_storage[ctx.id] = ctx
    ctx = pipeline(DreamMessage(text=last_request), ctx.id)
    response = get_response(ctx, pipeline.actor)
    del pipeline.context_storage[ctx.id]
    return response
