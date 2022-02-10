import logging

import df_engine.conditions as cnd
from df_engine.core import Actor
from df_engine.core.keywords import GLOBAL, LOCAL, PROCESSING, RESPONSE, TRANSITIONS

import common.dff.integration.processing as int_prs

import scenario.condition as loc_cnd
import scenario.response as rsp

logger = logging.getLogger(__name__)

ZERO_CONFIDENCE = 0.0

flows = {
    GLOBAL: {
        TRANSITIONS: {("funfact", "thematic", 1.1): loc_cnd.thematic_funfact_condition},
    },
    "service": {
        LOCAL: {TRANSITIONS: {("funfact", "random"): loc_cnd.random_funfact_condition}},
        "start": {RESPONSE: ""},
        "fallback": {
            PROCESSING: {"set_confidence": int_prs.set_confidence(ZERO_CONFIDENCE)},
            RESPONSE: "",
        },
    },
    "funfact": {
        LOCAL: {
            TRANSITIONS: {
                ("funfact", "random"): cnd.any([loc_cnd.random_funfact_condition, loc_cnd.another_funfact_condition])
            }
        },
        "random": {RESPONSE: rsp.random_funfact_response},
        "thematic": {RESPONSE: rsp.thematic_funfact_response},
    },
}

actor = Actor(flows, start_label=("service", "start"), fallback_label=("service", "fallback"))
