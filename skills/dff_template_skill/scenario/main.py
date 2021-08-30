import logging
import re

from dff.core.keywords import TRANSITIONS, GRAPH, RESPONSE, GLOBAL_TRANSITIONS
from dff.core import Actor
import dff.conditions as cnd
import dff.transitions as trn

import common.dff.integration.condition as int_cnd
# from . import condition as loc_cnd
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
                RESPONSE: "Hi, how are you?",  # When the agent goes to node1, we return "Hi, how are you?"
                TRANSITIONS: {"node2": cnd.regexp(r"how are you", re.IGNORECASE)},
            },
            "node2": {
                RESPONSE: "Good. What do you want to talk about?",
                TRANSITIONS: {"node3": cnd.regexp("Let's talk about .*", re.IGNORECASE)},
            },
            "node3": {
                RESPONSE: "Sorry, I can not talk about that now. Maybe late. Do you like science?",
                TRANSITIONS: {
                    "node4": int_cnd.is_yes_vars,
                    "node5": int_cnd.is_no_vars,
                    "node7": int_cnd.is_do_not_know_vars,
                },
            },
            "node4": {
                RESPONSE: "I like science too",
                TRANSITIONS: {("node7", 0.1): cnd.true},
            },
            "node5": {
                RESPONSE: "I do not like science too",
                TRANSITIONS: {("node7", 0.1): cnd.true},
            },
            "node6": {
                RESPONSE: "I do known science too",
                TRANSITIONS: {("node7", 0.1): cnd.true},
            },
            "node7": {
                RESPONSE: "bye",
            },
        }
    },
}


actor = Actor(flows, start_node_label=("global", "start"), fallback_node_label=("global", "fallback"))
