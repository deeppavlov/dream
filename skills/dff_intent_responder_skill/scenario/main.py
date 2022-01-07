import logging

import df_engine.conditions as cnd
from df_engine.core import Actor
from df_engine.core.keywords import GLOBAL, LOCAL, PROCESSING, RESPONSE, TRANSITIONS

import common.dff.integration.processing as int_prs

#import scenario.condition as loc_cnd
import scenario.response as rsp

logger = logging.getLogger(__name__)

ZERO_CONFIDENCE = 0.0

flows = {
    "service": {
        "start": {RESPONSE: ""},
        "fallback": {RESPONSE: "", PROCESSING: {"set_confidence": int_prs.set_confidence(ZERO_CONFIDENCE)}},
    },
    GLOBAL: {
        TRANSITIONS: {("simple", "random"): cnd.true()},
    },
    "simple": {
        "random": {RESPONSE: rsp.exit_respond},
    },
}

actor = Actor(flows, start_label=("service", "start"), fallback_label=("service", "fallback"))
