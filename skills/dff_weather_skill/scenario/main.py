import dff.conditions as cnd
from dff.core import Actor
from dff.core.keywords import PROCESSING, RESPONSE, TRANSITIONS

import common.dff.integration.condition as int_cnd
import common.dff.integration.processing as int_prs
from common.constants import CAN_CONTINUE_SCENARIO
from common.weather import ASK_WEATHER_SKILL_PHRASE
from scenario.condition import (
    chat_about_weather_condition,
    forecast_intent_condition,
    forecast_requested_condition,
    homeland_forecast_requested_condition,
    request_with_location_condition,
)
from scenario.constants import HIGH_CONF, ZERO_CONF
from scenario.processing import location_request_processing
from scenario.response import activity_answer_response, activity_question_response, forecast_response

flows = {
    "service": {
        "start": {
            RESPONSE: "",
            TRANSITIONS: {
                ("weather", "forecast"): cnd.any(
                    [
                        homeland_forecast_requested_condition,
                        cnd.all(
                            [
                                request_with_location_condition,
                                cnd.any([forecast_requested_condition, forecast_intent_condition]),
                            ]
                        ),
                    ]
                ),
                ("weather", "location_request"): cnd.any([forecast_requested_condition, forecast_intent_condition]),
                ("weather", "continue_question"): chat_about_weather_condition,
            },
        },
        "fallback": {
            RESPONSE: "Oops",
            PROCESSING: {"set_confidence": int_prs.set_confidence(ZERO_CONF)},
        },
    },
    "weather": {
        "forecast": {RESPONSE: forecast_response, TRANSITIONS: {"activity_question": cnd.true()}},
        "location_request": {
            RESPONSE: "Hmm. Which particular city would you like a weather forecast for?",
            PROCESSING: {"location_request_processing": location_request_processing},
            TRANSITIONS: {"forecast": cnd.true()},
        },
        "continue_question": {
            RESPONSE: ASK_WEATHER_SKILL_PHRASE,
            PROCESSING: {"set_confidence": int_prs.set_confidence(HIGH_CONF)},
            TRANSITIONS: {
                "forecast": cnd.all([int_cnd.is_yes_vars, request_with_location_condition]),
                "location_request": int_cnd.is_yes_vars,
            },
        },
        "activity_question": {
            RESPONSE: activity_question_response,
            PROCESSING: {"set_confidence": int_prs.set_confidence(CAN_CONTINUE_SCENARIO)},
            TRANSITIONS: {"activity_answer": cnd.true()},
        },
        "activity_answer": {RESPONSE: activity_answer_response},
    },
}

actor = Actor(flows, start_label=("service", "start"), fallback_label=("service", "fallback"))
