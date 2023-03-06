import logging
import re

from df_engine.core.keywords import LOCAL, PROCESSING, TRANSITIONS, RESPONSE, GLOBAL
from df_engine.core import Actor
import df_engine.conditions as cnd
import df_engine.labels as lbl

import common.dff.integration.condition as int_cnd
import common.dff.integration.processing as int_prs
import common.dff.integration.response as int_rsp


import common.constants as common_constants

from . import condition as loc_cnd
from . import response as loc_rsp

logger = logging.getLogger(__name__)

flows = {
    GLOBAL: {
        TRANSITIONS: {
            ("greeting", "caption"): loc_cnd.voice_message_detected
            #("greeting", "short_sound"): loc_cnd.short_sound,
            #("greeting", "long_sound"): loc_cnd.long_sound
        },
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
        "short_sound": {
            RESPONSE: loc_rsp.short_response,
            PROCESSING: {},
            TRANSITIONS: {},
        },
        "long_sound": {
            RESPONSE: loc_rsp.long_response,
            PROCESSING: {},
            TRANSITIONS: {},
        }
    },
    "global_flow": {
        "start": {
            RESPONSE: "Darova",
            TRANSITIONS: {},
        },
        "fallback": {
            RESPONSE: "IM BROKEN AAAAAA",
            TRANSITIONS: {},
        }
    }
}


actor = Actor(flows, start_label=("global_flow", "start"), fallback_label=("global_flow", "fallback"))
