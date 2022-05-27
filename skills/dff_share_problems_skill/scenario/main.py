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

from common.gain_assistance import DEPRESSION_PATTERN, BAD_DAY_PATTERN, PROBLEMS_PATTERN
from common.constants import GOAL_IN_PROGRESS, GOAL_ACHIEVED, GOAL_NOT_ACHIEVED, GOAL_OFFERED

import common.set_goal_flag as goal_status

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
            ("gain_assistance", "send2specialist"): cnd.regexp(DEPRESSION_PATTERN),
            ("gain_assistance", "bad_day"): cnd.regexp(BAD_DAY_PATTERN),
            ("gain_assistance", "try2comfort"): cnd.regexp(PROBLEMS_PATTERN)
        },
    },
    "sevice": {
        "start": {
            RESPONSE: "",
            TRANSITIONS: {
                ("gain_assistance", "send2specialist"): cnd.regexp(DEPRESSION_PATTERN),
                ("gain_assistance", "bad_day"): cnd.regexp(BAD_DAY_PATTERN),
                ("gain_assistance", "try2comfort"): cnd.regexp(PROBLEMS_PATTERN)
            },
        },
        "fallback": {
            RESPONSE: "Sorry, but I don't understand what you've just said :(",
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(0.0),
                "set_can_continue": int_prs.set_can_continue(common_constants.CAN_NOT_CONTINUE),
            },
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
            RESPONSE: "I'm very sorry for you... But I belive that a psychologist can help you in this situation. "
            "As for now, do you have someone you can call and ask to help you?",
            PROCESSING: {
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {
                "has_close_person": int_cnd.is_yes_vars,
                "no_close_person": int_cnd.is_no_vars
            }
        },
        "has_close_person": {
            RESPONSE: "Please speak to this person and try to calm down. I hope you're going to feel better.",
            PROCESSING: {
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_ACHIEVED)
            }
        },
        "no_close_person": {
            RESPONSE: "Try to calm down and make sure to get help from the specialist. I hope you're going to feel better",
            PROCESSING: {
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_ACHIEVED)
            }
        }, 
        "bad_day": {
            RESPONSE: "I'm sorry you had a hard day. Do you want to know how my day was?", 
            PROCESSING: {
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {
                "bot_day": int_cnd.is_yes_vars,
                "goodbye_node": int_cnd.is_no_vars
            },
        },
        "bot_day": {
            RESPONSE: "The servers crashed today and I thought I was dead."
            " But then I woke up and saw a message from the best user in the world (you)."
            " I believe there is always something that can make day better!",
            PROCESSING: {
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_ACHIEVED)
            }
        },
        "goodbye_node": {
            RESPONSE: "Ok. Let's speak about something else then.",
             PROCESSING: {
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_NOT_ACHIEVED)
            }
        },
        "try2comfort": {
            RESPONSE: "Do you want to discuss it?",
            PROCESSING: {
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
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
            PROCESSING: {
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_ACHIEVED)
            },
        },
        "clarify": {
            RESPONSE: "What happened?",
            PROCESSING: {
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {
                "gratitude": cnd.true()
            },
        },
    },
}


actor = Actor(flows, start_label=("sevice", "start"), fallback_label=("sevice", "fallback"))
