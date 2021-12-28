from df_engine.core import Actor, Context

from common.constants import CAN_CONTINUE_SCENARIO, CAN_NOT_CONTINUE
from common.dff.integration.condition import is_yes_vars
from common.dff.integration.context import (
    get_dialog,
    get_last_human_utterance,
    get_shared_memory,
    save_to_shared_memory,
    set_can_continue,
    set_confidence,
)
from scenario.condition import homeland_forecast_requested_condition
from scenario.constants import MISSED_CITY_CONF, QUESTION_PHRASE, SMALLTALK_CONF, SORRY_PHRASE, ZERO_CONF
from scenario.processing import forecast_intent_processing
from scenario.utils import (
    WEATHER_DICT,
    get_preferred_weather,
    request_weather_service,
    retrieve_location_entity_from_utterance,
)


def forecast_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    location_name = ""
    if homeland_forecast_requested_condition(ctx, actor):
        dialog = get_dialog(ctx, actor)
        if "human" in dialog and "profile" in dialog["human"]:
            location_name = dialog["human"]["profile"].get("location", "")
    else:
        human_utter = get_last_human_utterance(ctx, actor)
        location_name = retrieve_location_entity_from_utterance(human_utter)
    if location_name:
        forecast_intent_processing(ctx, actor)
        response = f"{request_weather_service(location_name)}. {QUESTION_PHRASE}"
    else:
        set_can_continue(ctx, actor, CAN_CONTINUE_SCENARIO)
        set_confidence(ctx, actor, MISSED_CITY_CONF)
        response = SORRY_PHRASE
    return response


def activity_question_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    response = ""
    preferred_weather = get_preferred_weather(ctx.last_request, WEATHER_DICT)
    if preferred_weather:
        save_to_shared_memory(ctx, actor, preferred_weather=preferred_weather)
        set_confidence(ctx, actor, SMALLTALK_CONF)
        response = WEATHER_DICT[preferred_weather]["question"]
    else:
        set_confidence(ctx, actor, ZERO_CONF)
    return response


def activity_answer_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    response = ""
    if is_yes_vars(ctx, actor):
        set_can_continue(ctx, actor, CAN_NOT_CONTINUE)
        set_confidence(ctx, actor, SMALLTALK_CONF)
        shared_memory = get_shared_memory(ctx, actor)
        preferred_weather = shared_memory.get("preferred_weather", "")
        save_to_shared_memory(ctx, actor, preferred_weather="")
        if preferred_weather:
            response = WEATHER_DICT[preferred_weather]["answer"]
    else:
        set_can_continue(ctx, actor, CAN_NOT_CONTINUE)
        set_confidence(ctx, actor, ZERO_CONF)
    return response
