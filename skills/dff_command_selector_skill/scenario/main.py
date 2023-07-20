import logging

import df_engine.conditions as cnd
from df_engine.core import Actor
from df_engine.core.keywords import GLOBAL, PROCESSING, RESPONSE, TRANSITIONS

import scenario.response as rsp
import scenario.condition as loc_cnd
import common.dff.integration.processing as int_prs

logger = logging.getLogger(__name__)

ZERO_CONFIDENCE = 0.0

flows = {
    "service": {
        "start": {RESPONSE: ""},
        "fallback": {RESPONSE: "", PROCESSING: {"set_confidence": int_prs.set_confidence(ZERO_CONFIDENCE)}},
    },
    GLOBAL: {
        TRANSITIONS: {
            ("context_driven_response", "command_selector"): loc_cnd.command_selector_exists_condition,
            ("simple", "default"): cnd.true(),
        },
    },
    "context_driven_response": {
        "command_selector": {
            RESPONSE: rsp.command_selector_response,
            PROCESSING: {"set_confidence": rsp.set_confidence_from_input},
        },
    },
    "simple": {
        "default": {
            RESPONSE: rsp.default_response,
            PROCESSING: {"set_confidence": int_prs.set_confidence(ZERO_CONFIDENCE)},
        },
    },
}

actor = Actor(flows, start_label=("service", "start"), fallback_label=("service", "fallback"))
