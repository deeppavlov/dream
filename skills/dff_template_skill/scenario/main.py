import logging
import re

from dff.core.keywords import TRANSITIONS, GRAPH, RESPONSE, GLOBAL_TRANSITIONS
from dff.core import Actor
import dff.conditions as cnd
import dff.transitions as trn

import common.dff.integration.condition as int_cnd
# import .condition as loc_cnd

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
    "beatles": {
        GLOBAL_TRANSITIONS: {("beatles", "beatles_q"): cnd.regexp(r"\bbeatles\b", re.I)},
        GRAPH: {
            "start": {RESPONSE: ""},
            "beatles_q": {
                RESPONSE: "Do you like the Beatles?",
                # PROCESSING: set_confidence_and_continue_flag(1.0, common_constants.MUST_CONTINUE),
                TRANSITIONS: {
                    ("beatles_fact", "name"): int_cnd.is_yes_vars,
                    trn.forward(): cnd.true,
                },
            },
            "instruments_q": {
                RESPONSE: "Are you interested in musical instruments?",
                TRANSITIONS: {
                    # ("instruments", "play_q"): int_cnd.is_yes_vars,
                    # ("photos", "photos_q"): cnd.true,
                },
            },
        },
    },
    "beatles_fact": {
        GRAPH: {
            "name": {
                RESPONSE: "Beatles... Sound like a wordplay, doesn’t it? Beetles making the beat. "
                "That’s how they meant it",
                # TRANSITIONS: {("album", "what_album"): cnd.true},
            }
        },
    },
}


actor = Actor(flows, start_node_label=("beatles", "start"))
