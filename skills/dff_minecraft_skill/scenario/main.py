import logging
import re

from df_engine.core.keywords import LOCAL, PROCESSING, TRANSITIONS, RESPONSE, GLOBAL
from df_engine.core import Context, Actor
import df_engine.conditions as cnd
import df_engine.labels as lbl
from .processing import GO_TO_COMPILED_PATTERN

import common.dff.integration.condition as int_cnd
import common.dff.integration.processing as int_prs
import common.dff.integration.response as int_rsp
import common.minecraft.core.serializer as serializer


import common.constants as common_constants

from . import condition as loc_cnd
from . import response as loc_rsp
from . import processing as loc_prs

logger = logging.getLogger(__name__)

# First of all, to create a dialog agent, we need to create a dialog script.
# Below, `flows` is the dialog script.
# A dialog script is a flow dictionary that can contain multiple flows .
# Flows are needed in order to divide a dialog into sub-dialogs and process them separately.
# For example, the separation can be tied to the topic of the dialog.
# In our example, there is one flow called greeting_flow.

# Inside each flow, we can describe a sub-dialog using keyword `GRAPH` from df_engine.core.keywords module.
# Here we can also use keyword `GLOBAL_TRANSITIONS`, which we have considered in other examples.

# `GRAPH` describes a sub-dialog using linked nodes, each node has the keywords `RESPONSE` and `TRANSITIONS`.

# `RESPONSE` - contains the response that the dialog agent will return when transitioning to this node.
# `TRANSITIONS` - describes transitions from the current node to other nodes.
# `TRANSITIONS` are described in pairs:
#      - the node to which the agent will perform the transition
#      - the condition under which to make the transition

# "goto": default_response,
#         "goto_user": default_response,
#         "stop": default_response,
#         "destroy_block": default_response,
#         "place_block": default_response,
#         "destroy_and_grab_block": default_response,
#         "look_at_user": default_response

flows = {
    GLOBAL: 
    {
        TRANSITIONS: {
                ("commands", "goto_user"): loc_cnd.is_intent("goto_user"),
                ("commands", "goto"): loc_cnd.is_intent("goto"),
                ("commands", "follow_me"): loc_cnd.is_intent("follow_me"),
                ("commands", "stop"): loc_cnd.is_intent("stop"),
                ("commands", "destroy_block"): loc_cnd.is_intent("destroy_block"),
                ("commands", "place_block"): loc_cnd.is_intent("place_block"),
                ("commands", "destroy_and_grab_block"): loc_cnd.is_intent("destroy_and_grab_block"),
                ("commands", "look_at_user"): loc_cnd.is_intent("look_at_user"),
        }
    },
    "service": {
         "start": {RESPONSE: ""},
        "fallback": {
            RESPONSE: "Sorry, I don't know this command yet. You can ask me to 'go to X, Y, Z'!",
            TRANSITIONS: {
                lbl.previous(): cnd.regexp(r"previous", re.IGNORECASE),
                lbl.repeat(0.2): cnd.true(),
            },
        },
    },
    "commands": {
        "goto": {
            PROCESSING: {
                1: loc_prs.add_encoding_for_goto()
                },
            RESPONSE: loc_rsp.response_for_intent("goto"),
            TRANSITIONS: {},
        },
        "goto_user": {
            PROCESSING: {
                1: loc_prs.add_encoding("goto_user")
                },
            RESPONSE: loc_rsp.response_for_intent("goto_user"),
            TRANSITIONS: {},
        },
        "follow_me": {
            PROCESSING: {
                1: loc_prs.add_encoding("goto_user", should_follow = True)
                },
            RESPONSE: loc_rsp.response_for_intent("follow_me"),
            TRANSITIONS: {},
        },
        "stop": {
            PROCESSING: {
                1: loc_prs.add_encoding_for_stop()
                },
            RESPONSE: loc_rsp.response_for_intent("stop"),
            TRANSITIONS: {},
        },
        "destroy_block": {
            PROCESSING: {
                1: loc_prs.add_encoding_no_range("destroy_block")
                },
            RESPONSE: loc_rsp.response_for_intent("destroy_block"),
            TRANSITIONS: {},
        },
        "place_block": {
            PROCESSING: {
                1: loc_prs.add_encoding_no_range("place_block")
                },
            RESPONSE: loc_rsp.response_for_intent("place_block"),
            TRANSITIONS: {},
        },
        "destroy_and_grab_block": {
            PROCESSING: {
                1: loc_prs.add_encoding_no_range("destroy_and_grab_block")
                },
            RESPONSE: loc_rsp.response_for_intent("destroy_and_grab_block"),
            TRANSITIONS: {},
        },
        "look_at_user": {
            PROCESSING: {
                1: loc_prs.add_encoding_for_look_at_user()
                },
            RESPONSE: loc_rsp.response_for_intent("look_at_user"),
            TRANSITIONS: {},
        },
    },
}


actor = Actor(flows, start_label=("service", "start"), fallback_label=("service", "fallback"))


# ZERO_CONFIDENCE = 0.0

# flows = {
#     "service": {
#         "start": {RESPONSE: ""},
#         "fallback": {RESPONSE: "", PROCESSING: {"set_confidence": int_prs.set_confidence(ZERO_CONFIDENCE)}},
#     },
#     GLOBAL: {
#         TRANSITIONS: {
#             ("context_driven_response", "minecraft_intents"): loc_cnd.minecraft_intent_exists_condition,
#             ("simple", "default"): cnd.true(),
#         },
#     },
#     "context_driven_response": {
#         "minecraft_intents": {
#             RESPONSE: loc_rsp.minecraft_intents_response,
#             PROCESSING: {"set_confidence": loc_rsp.set_confidence_from_input},
#         },
#     },
#     "simple": {
#         "default": {
#             RESPONSE: loc_rsp.default_response,
#             PROCESSING: {
#                 1: loc_prs.add_encoding_for_goto("goto"),
#                 2: loc_prs.add_encoding("goto_user", True), # follow me continuously
#                 "set_confidence" : int_prs.set_confidence(ZERO_CONFIDENCE),
#                 },
#         },
#     },
# }

# actor = Actor(flows, start_label=("service", "start"), fallback_label=("service", "fallback"))
