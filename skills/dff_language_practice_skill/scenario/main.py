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
from . import processing as loc_prs

logger = logging.getLogger(__name__)


flows = {
    GLOBAL: {
        TRANSITIONS: {
            ("scenario", "cancel_dialog"): cnd.regexp(r"\b(stop|finish|quit)\b", re.IGNORECASE),
            ("scenario", "repeat"): cnd.regexp(r"\brepeat\b", re.IGNORECASE),
            ("scenario", "previous"): cnd.regexp(r"\bprevious\b", re.IGNORECASE),
            ("scenario", "intro"): loc_cnd.is_intro(),
            ("scenario", "is_known_question"): cnd.all([int_cnd.is_question, loc_cnd.is_known_question()]),
            ("scenario", "not_known_question"): int_cnd.is_question,
            ("scenario", "bot_question"): cnd.true(),
        },
    },
    "service": {
        "start": {
            RESPONSE: "",
            TRANSITIONS: {("scenario", "intro"): loc_cnd.is_intro()},
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
        "intro": {
            RESPONSE: loc_rsp.intro_response(),
            PROCESSING: {},
            TRANSITIONS: {},
        },
        "is_known_question": {
            RESPONSE: loc_rsp.answer_known_question(),
            PROCESSING: {},
            TRANSITIONS: {},
        },
        "not_known_question": {
            RESPONSE: "That's a good question! Unfortunately, I don't know the answer yet.",
            PROCESSING: {},
            TRANSITIONS: {},
        },
        "bot_question": {
            RESPONSE: loc_rsp.follow_scenario_response(),
            PROCESSING: {},
            TRANSITIONS: {
                "cancel_dialog": cnd.regexp(r"\b(stop|finish|quit)\b", re.IGNORECASE),
                "repeat": cnd.regexp(r"\brepeat\b", re.IGNORECASE),
                "is_known_question": cnd.all([int_cnd.is_question, loc_cnd.is_known_question()]),
                "not_known_question": int_cnd.is_question,
                "acknowledgement": loc_cnd.is_acknowledgement(),
            },
        },
        "acknowledgement": {
            RESPONSE: loc_rsp.acknowledgement_response(),
            PROCESSING: {},
            TRANSITIONS: {},
        },
        "cancel_dialog": {
            RESPONSE: "Ok, let's finish here. Would you like me to comment on your performance?",
            PROCESSING: {},
            TRANSITIONS: {"no_feedback_needed": int_cnd.is_no_vars},
        },
        "no_feedback_needed": {RESPONSE: "As you wish!"},
        "repeat": {
            RESPONSE: loc_rsp.repeat_response(),
            PROCESSING: {},
            TRANSITIONS: {},
        },
        "previous": {
            RESPONSE: loc_rsp.previous_response(),
            PROCESSING: {},
            TRANSITIONS: {},
        },
    },
}


actor = Actor(flows, start_label=("service", "start"), fallback_label=("service", "fallback"))
