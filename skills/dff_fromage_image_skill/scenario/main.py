import logging

from df_engine.core.keywords import TRANSITIONS, RESPONSE, PROCESSING, GLOBAL, LOCAL
from df_engine.core import Actor

import common.dff.integration.processing as int_prs

from . import condition as loc_cnd
from . import response as loc_rsp

logger = logging.getLogger(__name__)

flows = {
    GLOBAL: {
        TRANSITIONS: {("response", "caption"): loc_cnd.caption_condition},
    },
    "response": {
        LOCAL: {
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(1.0),
                "set_can_continue": int_prs.set_can_continue(),
            },
        },
        "caption": {
            RESPONSE: loc_rsp.generic_response,
            PROCESSING: {},
            TRANSITIONS: {},
        },
    },
    "global_flow": {
        "start": {
            TRANSITIONS: {},
        },
        "fallback": {
            TRANSITIONS: {},
        },
    },
}

actor = Actor(flows, start_label=("global_flow", "start"), fallback_label=("global_flow", "fallback"))
