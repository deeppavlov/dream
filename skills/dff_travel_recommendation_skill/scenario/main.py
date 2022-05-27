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
from common.travel_recommendation import TRAVEL_RECOMMENDATION_PATTERN

import common.set_goal_flag as goal_status
from common.constants import GOAL_DETECTED, GOAL_IN_PROGRESS, GOAL_ACHIEVED, GOAL_NOT_ACHIEVED, GOAL_OFFERED


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

flows = {
    GLOBAL: {
        TRANSITIONS: {
            ("travel", "country_0"): cnd.regexp(TRAVEL_RECOMMENDATION_PATTERN),
        },
    },
    "sevice": {
        "start": {
            RESPONSE: "",
            TRANSITIONS: {
                ("travel", "country_0"): cnd.regexp(TRAVEL_RECOMMENDATION_PATTERN)
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
    "travel": {
        LOCAL: {
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(1.0),
                "set_can_continue": int_prs.set_can_continue()
            },
        },
        "country_0": {
            RESPONSE: "Have you been to {country0}?",
            PROCESSING: {
                "choose_countries2recommend": loc_prs.choose_countries2recommend(),
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {
                "not_visited_country_0": int_cnd.is_no_vars,
                "visited_country_0": int_cnd.is_yes_vars
            },
        },
        "not_visited_country_0": {
            RESPONSE: "Then I highly recommend it to you! You should go to {capital0} and see {sight0}. "
                    "{description0} {climate0} {best_time0}",
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_ACHIEVED)
            },
        },
        "visited_country_0": {
            RESPONSE: "And have you been in {capital0}?",
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {
                "not_visited_capital_0": int_cnd.is_no_vars,
                "visited_capital_0": int_cnd.is_yes_vars
            },
        },
        "not_visited_capital_0": {
            RESPONSE: "Then you should go to there and see {sight0}. "
                    "{description0} {climate0} {best_time0}",
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_ACHIEVED)
            },
        },
        "visited_capital_0": {
            RESPONSE: "Did you like {sight0}?",
             PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {
                ("country_1", 0.1): cnd.true()
            },
        },
        "country_1": {
            RESPONSE: "Have you been to {country1}?",
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {
                "not_visited_country_1": int_cnd.is_no_vars,
                "visited_country_1": int_cnd.is_yes_vars
            },
        },
        "not_visited_country_1": {
            RESPONSE: "Then I highly recommend it to you! You should go to {capital1} and see {sight1}. "
                    "{description1} {climate1} {best_time1}",
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_ACHIEVED)
            },
        },
        "visited_country_1": {
            RESPONSE: "And have you been in {capital1}?",
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {
                "not_visited_capital_1": int_cnd.is_no_vars,
                "visited_capital_1": int_cnd.is_yes_vars
            },
        },
        "not_visited_capital_1": {
            RESPONSE: "Then you should go to there and see {sight1}. "
                    "{description1} {climate1} {best_time1}",
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_ACHIEVED)
            },
        },
        "visited_capital_1": {
            RESPONSE: "Did you like {sight1}?",
             PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {
                ("country_2", 0.1): cnd.true()
            },
        },
        "country_2": {
            RESPONSE: "Have you been to {country2}?",
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {
                "not_visited_country_2": int_cnd.is_no_vars,
                "visited_country_2": int_cnd.is_yes_vars
            },
        },
        "not_visited_country_2": {
            RESPONSE: "Then I highly recommend it to you! You should go to {capital2} and see {sight2}. "
                    "{description2} {climate2} {best_time2}",
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_ACHIEVED)
            },
        },
        "visited_country_2": {
            RESPONSE: "And have you been in {capital2}?",
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {
                "not_visited_capital_2": int_cnd.is_no_vars,
                "visited_capital_2": int_cnd.is_yes_vars
            },
        },
        "not_visited_capital_2": {
            RESPONSE: "Then you should go to there and see {sight2}. "
                    "{description2} {climate2} {best_time2}",
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_ACHIEVED)
            },
        },
        "visited_capital_2": {
            RESPONSE: "Did you like {sight2}?",
             PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {
                ("visited_all", 0.1): cnd.true()
            },
        },
        "visited_all": {
            RESPONSE: "Wow! You've visited many good places! Maybe next time I'll find some new places for you to visit!",
            PROCESSING: {
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_NOT_ACHIEVED)
            }
        }
    },
}


actor = Actor(flows, start_label=("sevice", "start"), fallback_label=("sevice", "fallback"))
