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

flows = {
    GLOBAL: {
        TRANSITIONS: {
            ("gain_assistance", "send2specialist"): loc_cnd.has_forbidden_words(),
            ("gain_assistance", "bad_day"): loc_cnd.has_bad_day_words(),
            ("gain_assistance", "try2comfort"): loc_cnd.has_relationship_words()
        },
    },
    "sevice": {
        "start": {
            RESPONSE: "",
            TRANSITIONS: {("gain_assistance", "send2specialist"): cnd.true()},
        },
        "fallback": {
            RESPONSE: "Ooops",
            TRANSITIONS: {
                lbl.previous(): cnd.regexp(r"previous", re.IGNORECASE),
                lbl.repeat(0.2): cnd.true(),
            },
        },
    },
    "gain_assistance": {
        LOCAL: {
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(1.0),
                "set_can_continue": int_prs.set_can_continue()
            },
        },
        "send2specialist": {
            RESPONSE: "I'm very sorry for you... But I belive that a psychologist can help you in this situation",
        },
        "bad_day": {
            RESPONSE: "I'm sorry you had a hard day. Do you want to know how my day was?",
            TRANSITIONS: {
                "bot_day": int_cnd.is_yes_vars,
                "goodbye_node": int_cnd.is_no_vars
            },
        },
        "bot_day": {
            RESPONSE: "The servers crashed today and I thought I was dead."
            " But then I woke up and saw a message from the best user in the world (you)",
        },
        "goodbye_node": {
            RESPONSE: "Ok. Maybe I can cheer you up some other way",
        },
        "try2comfort": {
            RESPONSE: "Do you want to discuss it?",
            TRANSITIONS: {
                "gratitude": cnd.all(
                    [int_cnd.is_yes_vars, loc_cnd.is_detailed()]
                ),
                "clarify": int_cnd.is_yes_vars,
                "goodbye_node": int_cnd.is_no_vars
            },
        },
        "gratitude": {
            RESPONSE: "I'm sorry to hear that. Thank you for sharing this with me.",
        },
        "clarify": {
            RESPONSE: "What happened?",
            TRANSITIONS: {
                "gratitude": cnd.true()
            },
        },
    },
}


actor = Actor(flows, start_label=("sevice", "start"), fallback_label=("sevice", "fallback"))
