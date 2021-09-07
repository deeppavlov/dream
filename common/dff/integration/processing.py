import logging

from dff.core import Node, Context, Actor

import common.constants as common_constants
from . import context


logger = logging.getLogger(__name__)


def save_slots_to_ctx(slots: dict):
    def save_slots_to_ctx_processing(
        node_label: str,
        node: Node,
        ctx: Context,
        actor: Actor,
        *args,
        **kwargs,
    ) -> tuple[str, Node]:
        ctx.misc["slots"] = ctx.misc.get("slots", {}) | slots
        return node_label, node

    return save_slots_to_ctx_processing


def fill_responses_by_slots():
    def fill_responses_by_slots_processing(
        node_label: str,
        node: Node,
        ctx: Context,
        actor: Actor,
        *args,
        **kwargs,
    ) -> tuple[str, Node]:
        for slot_name, slot_value in ctx.misc.get("slots", {}).items():
            node.response = node.response.replace("{" f"{slot_name}" "}", slot_value)
        return node_label, node

    return fill_responses_by_slots_processing


def set_confidence(confidence: float = 1.0):
    def set_confidence_processing(
        node_label: str,
        node: Node,
        ctx: Context,
        actor: Actor,
        *args,
        **kwargs,
    ) -> tuple[str, Node]:
        context.set_confidence(ctx, actor, confidence)
        return node_label, node

    return set_confidence_processing


def set_can_continue(continue_flag: str = common_constants.CAN_CONTINUE_SCENARIO):
    def set_can_continue_processing(
        node_label: str,
        node: Node,
        ctx: Context,
        actor: Actor,
        *args,
        **kwargs,
    ) -> tuple[str, Node]:
        context.set_can_continue(ctx, actor, continue_flag)
        return node_label, node

    return set_can_continue_processing
