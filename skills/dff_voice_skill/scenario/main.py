import logging

from df_engine.core.keywords import LOCAL, PROCESSING, TRANSITIONS, RESPONSE, GLOBAL
from df_engine.core import Actor

import common.dff.integration.processing as int_prs

from . import condition as loc_cnd
from . import response as loc_rsp

logger = logging.getLogger(__name__)

flows = {
    GLOBAL: {
        TRANSITIONS: {("greeting", "caption"): loc_cnd.voice_message_detected},
    },
    "greeting": {
        LOCAL: {
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(1.0),
                "set_can_continue": int_prs.set_can_continue(),
            },
        },
        "caption": {
            RESPONSE: loc_rsp.caption,
            PROCESSING: {},
            TRANSITIONS: {},
        },
    },
    "global_flow": {
        "start": {
            RESPONSE: "The voice skill is now active and running.",
            TRANSITIONS: {},
        },
        "fallback": {
            RESPONSE: "An exception occured while accessing voice skill.",
            TRANSITIONS: {},
        },
    },
}


actor = Actor(flows, start_label=("global_flow", "start"), fallback_label=("global_flow", "fallback"))
