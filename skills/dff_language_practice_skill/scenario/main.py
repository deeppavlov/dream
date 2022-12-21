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
            ("greeting", "node1"): cnd.regexp(r"\balemira\b"),
        },
    },
    "sevice": {
        "start": {
            RESPONSE: "",
            TRANSITIONS: {("greeting", "node1"): cnd.true()},
        },
        "fallback": {
            RESPONSE: "Ooops",
            TRANSITIONS: {
                lbl.previous(): cnd.regexp(r"previous", re.IGNORECASE),
                lbl.repeat(0.2): cnd.true(),
            },
        },
    },
    "greeting": {
        LOCAL: {
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(0.9),
                "set_can_continue": int_prs.set_can_continue(),
            },
        },
        "node1": {
            RESPONSE: loc_rsp.response_from_data(),  
            PROCESSING: {},
            TRANSITIONS: {
                lbl.repeat(0.9): cnd.true(),
            },
        },
    },
}


actor = Actor(flows, start_label=("sevice", "start"), fallback_label=("sevice", "fallback"))
