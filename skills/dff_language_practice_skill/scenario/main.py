import logging
import re

from df_engine.core.keywords import LOCAL, PROCESSING, TRANSITIONS, RESPONSE, GLOBAL
from df_engine.core import Actor
import df_engine.conditions as cnd
import df_engine.labels as lbl

import common.dff.integration.condition as int_cnd
import common.dff.integration.processing as int_prs
import common.dff.integration.response as int_rsp

import common.set_user_instructions as set_instructions
import common.set_user_instructions as set_situation_description


import common.constants as common_constants

from . import condition as loc_cnd
from . import response as loc_rsp
from . import processing as loc_prs

logger = logging.getLogger(__name__)


flows = {
    GLOBAL: {
        TRANSITIONS: {("scenario", "main_node", 0.8): cnd.true()},
    },
    "service": {
        "start": {
            RESPONSE: "",
            TRANSITIONS: {("scenario", "main_node"): cnd.true()},
        },
        "fallback": {
            RESPONSE: "Ooops, something went wrong inside me! Could you repeat what you've just said?",
            TRANSITIONS: {
                lbl.previous(): cnd.regexp(r"previous", re.IGNORECASE),
                lbl.repeat(0.2): cnd.true(),
            },
        },
    },
    "scenario": {
        LOCAL: {
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(0.9),
                "set_can_continue": int_prs.set_can_continue(),
            },
        },
        "main_node": {
            RESPONSE: loc_rsp.response_from_data(),
            PROCESSING: {
                "set_user_instructions": set_instructions.set_user_instructions(),
                "set_situation_description": set_instructions.set_situation_description(),
                "slot_filling": int_prs.fill_responses_by_slots(),
            },
            TRANSITIONS: {
                "cancel_dialog": cnd.regexp(r"\b(stop|finish|quit)\b", re.IGNORECASE),
                lbl.repeat(0.9): cnd.true(),
            },
        },
        "cancel_dialog": {
            RESPONSE: "Ok, let's finish here. Would you like me to comment on your performance?",
            PROCESSING: {},
            TRANSITIONS: {"no_feedback_needed": int_cnd.is_no_vars},
        },
        "no_feedback_needed": {RESPONSE: "As you wish!"},
    },
}


actor = Actor(flows, start_label=("service", "start"), fallback_label=("service", "fallback"))
