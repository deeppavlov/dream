from typing import Optional

from dff.core import Actor, Context, Node

from common.constants import CAN_CONTINUE_SCENARIO, MUST_CONTINUE
from common.dff.integration.context import set_can_continue, set_confidence
from scenario.condition import forecast_intent_condition, forecast_requested_condition
from scenario.constants import HIGH_CONF, QUESTION_CONF


def location_request_processing(
    ctx: Context,
    actor: Actor,
    *args,
    **kwargs,
) -> Optional[tuple[str, Node]]:
    forecast_intent_processing(ctx, actor)
    return ctx


def forecast_intent_processing(ctx, actor) -> None:
    if not forecast_requested_condition(ctx, actor) and forecast_intent_condition(ctx, actor):
        set_can_continue(ctx, actor, CAN_CONTINUE_SCENARIO)
        set_confidence(ctx, actor, QUESTION_CONF)
    else:
        set_can_continue(ctx, actor, MUST_CONTINUE)
        set_confidence(ctx, actor, HIGH_CONF)
