import logging

import re

from df_engine.core.keywords import LOCAL, PROCESSING, TRANSITIONS, RESPONSE, GLOBAL
from df_engine.core import Actor
import df_engine.conditions as cnd
import df_engine.labels as lbl

import common.dff.integration.processing as int_prs

from . import response as loc_rsp
from . import condition as loc_cnd

logger = logging.getLogger(__name__)
# from log_utils import create_logger
# logger = create_logger(__file__)

# flows = {
#     GLOBAL: {
#         TRANSITIONS: {
#             ("greeting", "node1"): cnd.regexp(r"\bhi\b"),
#         },
#     },
#     "sevice": {
#         "start": {
#             RESPONSE: "",
#             TRANSITIONS: {("greeting", "node1"): cnd.true()},
#         },
#         "fallback": {
#             RESPONSE: "Ooops",
#             TRANSITIONS: {
#                 lbl.previous(): cnd.regexp(r"previous", re.IGNORECASE),
#                 lbl.repeat(0.2): cnd.true(),
#             },
#         },
#     },
#     "greeting": {
#         LOCAL: {
#             PROCESSING: {
#                 "set_confidence": int_prs.set_confidence(1.0),
#                 "set_can_continue": int_prs.set_can_continue(),
#             },
#         },
#         "node1": {
#             # RESPONSE: 'What is your name?',
#             RESPONSE: loc_rsp.find_name,
#             TRANSITIONS: {"node2": cnd.true()},
#         },
#         "node2": {
#             # RESPONSE: loc_rsp.find_name,
#             RESPONSE: "I've got your name already! Bye!"
#         },
#     },
# }

flows = {
    GLOBAL: {
        TRANSITIONS: {
            ("story_flow", "gpt_topic"): cnd.true(2.0),
            ("story_flow", "fallback_node"): cnd.neg(loc_cnd.has_story_intent),
        }
    },
    "story_flow": {
        "start_node": {
            RESPONSE: "",
            TRANSITIONS: {
                "gpt_topic": cnd.true(2.0),
            },
        },
        "fallback_node": {
            RESPONSE: 'Fallback!',
            TRANSITIONS: {
                "start_node": cnd.true(),
            },
        },
        "gpt_topic": {RESPONSE: loc_rsp.choose_topic,
                      TRANSITIONS: {
                          "gpt_story": cnd.true(2.0),
                          lbl.forward(): cnd.true()}},
        "gpt_story": {RESPONSE: loc_rsp.dummy_story},
    },
}

actor = Actor(flows, start_label=("story_flow", "start_node"), fallback_label=("story_flow", "fallback_node"))

# actor = Actor(flows, start_label=("sevice", "start"), fallback_label=("sevice", "fallback"))
# actor = Actor(flows, start_label=("story_flow", "start_node"), fallback_label=("story_flow", "fallback_node"))
