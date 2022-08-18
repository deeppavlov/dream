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
            ("greeting", "node1"): cnd.regexp(r"\bhi\b"),
        },
    },
    "sevice": {
        "start": {
            RESPONSE: "",
            # TRANSITIONS: {("greeting", "node1"): cnd.true()},
            TRANSITIONS: {"new_node1": cnd.true()},
        },
        "fallback": {
            RESPONSE: "Ooops",
            TRANSITIONS: {
                lbl.previous(): cnd.regexp(r"previous", re.IGNORECASE),
                lbl.repeat(0.2): cnd.true(),
            },
        },
        "new_node1": {
            # RESPONSE: 'What is your name?',
            RESPONSE: loc_rsp.find_name,
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(1.0),
                "set_can_continue": int_prs.set_can_continue()},
            TRANSITIONS: {"new_node2": cnd.true()},
        },
        "new_node2": {
            RESPONSE: loc_rsp.find_name,
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(1.0),
                "set_can_continue": int_prs.set_can_continue()},
            TRANSITIONS: {("greeting", "node1"): loc_cnd.example_lets_talk_about()},
        },
    },
    "greeting": {
        LOCAL: {
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(1.0),
                "set_can_continue": int_prs.set_can_continue(),
            },
        },
        "node1": {
            RESPONSE: 'What is your name?',
            TRANSITIONS: {"node2": cnd.true()},
        },
        "node2": {
            RESPONSE: loc_rsp.find_name,
        },
        "node3": {
            RESPONSE: "Sorry, I can not talk about that now. Maybe late. Do you like {topic}?",
            PROCESSING: {"fill_responses_by_slots": int_prs.fill_responses_by_slots()},
            TRANSITIONS: {
                "node4": int_cnd.is_yes_vars,
                "node5": int_cnd.is_no_vars,
                "node6": int_cnd.is_do_not_know_vars,
                "node7": cnd.true(),  # it will be chosen if other conditions are False
            },
        },
        "node4": {
            RESPONSE: "I like {topic} too, {user_name}",
            PROCESSING: {"fill_responses_by_slots": int_prs.fill_responses_by_slots()},
            TRANSITIONS: {("node7", 0.1): cnd.true()},
        },
        "node5": {
            RESPONSE: "I do not like {topic} too, {user_name}",
            PROCESSING: {"fill_responses_by_slots": int_prs.fill_responses_by_slots()},
            TRANSITIONS: {("node7", 0.1): cnd.true()},
        },
        "node6": {
            RESPONSE: "I have no opinion about {topic} too, {user_name}",
            PROCESSING: {"fill_responses_by_slots": int_prs.fill_responses_by_slots()},
            TRANSITIONS: {("node7", 0.1): cnd.true()},
        },
        "node7": {
            RESPONSE: int_rsp.multi_response(
                replies=["bye", "goodbye"],
                confidences=[1.0, 0.5],
                hype_attr=[
                    {"can_continue": common_constants.MUST_CONTINUE},  # for the first hyp
                    {"can_continue": common_constants.CAN_CONTINUE_SCENARIO},  # for the second hyp
                ],
            ),
            PROCESSING: {"set_confidence": int_prs.set_confidence(0.0)},
        },
    },
}

# flows = {
#     GLOBAL: {TRANSITIONS: {("story_flow", "fallback_node"): cnd.true()}},
#     "story_flow": {
#         "start_node": {
#             RESPONSE: "",
#             TRANSITIONS: {
#                 "choose_story_node": cnd.true()},
#         },
#         "choose_story_node": {
#             RESPONSE: 'You are on the first node!',
#             TRANSITIONS: {
#                 "which_story_node": cnd.true(),
#             },
#         },
#         "which_story_node": {
#             RESPONSE: "You are on the second node!",
#         },
#         "fallback_node": {
#             RESPONSE: 'This is fallback node!',
#             TRANSITIONS: {"start_node": cnd.true()},
#         },
#     },
# }


actor = Actor(flows, start_label=("sevice", "start"), fallback_label=("sevice", "fallback"))
# actor = Actor(flows, start_label=("story_flow", "start_node"), fallback_label=("story_flow", "fallback_node"))
