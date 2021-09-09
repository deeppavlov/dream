import logging
import re

from dff.core.keywords import PROCESSING, TRANSITIONS, GRAPH, RESPONSE, GLOBAL_TRANSITIONS
from dff.core import Actor
import dff.conditions as cnd
import dff.transitions as trn

import common.dff.integration.condition as int_cnd
import common.dff.integration.processing as int_prs
import common.dff.integration.response as int_rsp


import common.constants as common_constants

from . import condition as loc_cnd
from . import response as loc_rsp

# from . import processing as loc_prs

logger = logging.getLogger(__name__)

# First of all, to create a dialog agent, we need to create a dialog script.
# Below, `flows` is the dialog script.
# A dialog script is a flow dictionary that can contain multiple flows .
# Flows are needed in order to divide a dialog into sub-dialogs and process them separately.
# For example, the separation can be tied to the topic of the dialog.
# In our example, there is one flow called greeting_flow.

# Inside each flow, we can describe a sub-dialog using keyword `GRAPH` from dff.core.keywords module.
# Here we can also use keyword `GLOBAL_TRANSITIONS`, which we have considered in other examples.

# `GRAPH` describes a sub-dialog using linked nodes, each node has the keywords `RESPONSE` and `TRANSITIONS`.

# `RESPONSE` - contains the response that the dialog agent will return when transitioning to this node.
# `TRANSITIONS` - describes transitions from the current node to other nodes.
# `TRANSITIONS` are described in pairs:
#      - the node to which the agent will perform the transition
#      - the condition under which to make the transition

std_prs = [int_prs.set_confidence(1.0), int_prs.set_can_continue()]
flows = {
    "global": {
        GLOBAL_TRANSITIONS: {
            ("greeting", "node1"): cnd.regexp(r"\bhi\b"),
        },
        GRAPH: {
            "start": {
                RESPONSE: "",
                TRANSITIONS: {("greeting", "node1"): cnd.true},
            },
            "fallback": {
                RESPONSE: "Ooops",
                TRANSITIONS: {
                    trn.previous(): cnd.regexp(r"previous", re.IGNORECASE),
                    trn.repeat(0.2): cnd.true,
                },
            },
        },
    },
    "greeting": {
        GRAPH: {
            "node1": {
                RESPONSE: int_rsp.multi_response(replies=["Hi, how are you?", "Hi, what's up?"]),  # several hypothesis
                PROCESSING: std_prs + [int_prs.save_slots_to_ctx({"topic": "science", "user_name": "Gordon Freeman"})],
                TRANSITIONS: {"node2": cnd.regexp(r"how are you", re.IGNORECASE)},
            },
            "node2": {
                RESPONSE: loc_rsp.example_response("Good. What do you want to talk about?"),
                # loc_rsp.example_response is just for an example, you can use just str without example_response func
                PROCESSING: std_prs,
                TRANSITIONS: {"node3": loc_cnd.example_lets_talk_about()},
            },
            "node3": {
                RESPONSE: "Sorry, I can not talk about that now. Maybe late. Do you like {topic}?",
                PROCESSING: std_prs + [int_prs.fill_responses_by_slots()],
                TRANSITIONS: {
                    "node4": int_cnd.is_yes_vars,
                    "node5": int_cnd.is_no_vars,
                    "node6": int_cnd.is_do_not_know_vars,
                    "node7": cnd.true,  # it will be chosen if other conditions are False
                },
            },
            "node4": {
                RESPONSE: "I like {topic} too, {user_name}",
                PROCESSING: std_prs + [int_prs.fill_responses_by_slots()],
                TRANSITIONS: {("node7", 0.1): cnd.true},
            },
            "node5": {
                RESPONSE: "I do not like {topic} too, {user_name}",
                PROCESSING: std_prs + [int_prs.fill_responses_by_slots()],
                TRANSITIONS: {("node7", 0.1): cnd.true},
            },
            "node6": {
                RESPONSE: "I have no opinion about {topic} too, {user_name}",
                PROCESSING: std_prs + [int_prs.fill_responses_by_slots()],
                TRANSITIONS: {("node7", 0.1): cnd.true},
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
                PROCESSING: [int_prs.set_can_continue()],
            },
        }
    },
}


actor = Actor(flows, start_node_label=("global", "start"), fallback_node_label=("global", "fallback"))
