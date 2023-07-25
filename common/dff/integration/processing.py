import logging

from df_engine.core import Context, Actor
import common.constants as common_constants
from common.wiki_skill import extract_entity
from .facts_utils import provide_facts_response
from . import context


logger = logging.getLogger(__name__)


def save_slots_to_ctx(slots: dict):
    def save_slots_to_ctx_processing(
        ctx: Context,
        actor: Actor,
        *args,
        **kwargs,
    ) -> Context:
        ctx.misc["slots"] = ctx.misc.get("slots", {}) | slots
        return ctx

    return save_slots_to_ctx_processing


def entities(**kwargs):
    slot_info = list(kwargs.items())

    def extract_entities(
        ctx: Context,
        actor: Actor,
        *args,
        **kwargs,
    ) -> Context:
        for slot_name, slot_types in slot_info:
            if isinstance(slot_types, str):
                extracted_entity = extract_entity(ctx, slot_types)
                if extracted_entity:
                    ctx = save_slots_to_ctx({slot_name: extracted_entity})(ctx, actor)
            elif isinstance(slot_types, list):
                found = False
                for slot_type in slot_types:
                    if not slot_type.startswith("default:"):
                        extracted_entity = extract_entity(ctx, slot_type)
                        if extracted_entity:
                            ctx = save_slots_to_ctx({slot_name: extracted_entity})(ctx, actor)
                            found = True
                if not found:
                    default_value = ""
                    for slot_type in slot_types:
                        if slot_type.startswith("default:"):
                            default_value = slot_type.split("default:")[1]
                    if default_value:
                        ctx = save_slots_to_ctx({slot_name: default_value})(ctx, actor)
        return ctx

    return extract_entities


def fact_provider(page_source, wiki_page):
    def response(ctx: Context, actor: Actor, *args, **kwargs):
        return provide_facts_response(ctx, actor, page_source, wiki_page)

    return response


def fill_responses_by_slots():
    def fill_responses_by_slots_processing(
        ctx: Context,
        actor: Actor,
        *args,
        **kwargs,
    ) -> Context:
        processed_node = ctx.a_s.get("processed_node", ctx.a_s["next_node"])
        for slot_name, slot_value in ctx.misc.get("slots", {}).items():
            processed_node.response = processed_node.response.replace("{" f"{slot_name}" "}", slot_value)
        ctx.a_s["processed_node"] = processed_node
        return ctx

    return fill_responses_by_slots_processing


def set_confidence(confidence: float = 1.0):
    def set_confidence_processing(
        ctx: Context,
        actor: Actor,
        *args,
        **kwargs,
    ) -> Context:
        context.set_confidence(ctx, actor, confidence)
        return ctx

    return set_confidence_processing


def set_can_continue(continue_flag: str = common_constants.CAN_CONTINUE_SCENARIO):
    def set_can_continue_processing(
        ctx: Context,
        actor: Actor,
        *args,
        **kwargs,
    ) -> Context:
        context.set_can_continue(ctx, actor, continue_flag)
        return ctx

    return set_can_continue_processing
