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
from common.tv_series_recommendation import RECOMMEND_SERIES_PATTERN, MENTIONS_KNOWN_SERIES_PATTERN, MENTIONS_NETFLIX

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
            ("recommend_series", "series_q"): cnd.regexp(RECOMMEND_SERIES_PATTERN),
            ("mentions_known_series", "suggest2recommend"): cnd.regexp(MENTIONS_KNOWN_SERIES_PATTERN),
            ("mentions_netflix", "ask_last_series"): cnd.regexp(MENTIONS_NETFLIX)
        },
    },
    "sevice": {
        "start": {
            RESPONSE: "",
            TRANSITIONS: {
                ("recommend_series", "series_q"): cnd.regexp(RECOMMEND_SERIES_PATTERN),
                ("mentions_known_series", "suggest2recommend"): cnd.regexp(MENTIONS_KNOWN_SERIES_PATTERN)
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
    "recommend_series": {
        LOCAL: {
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(1.0),
                "set_can_continue": int_prs.set_can_continue(),
                "extract_random_series2recommend": loc_prs.extract_random_series2recommend()
            },
        },
        "series_q": {
            RESPONSE: 'Oh, I know a lot of Netflix series! Have you watched {random_series2recommend}?',
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {
                "watched_recommended": int_cnd.is_yes_vars,
                "not_watched_recommended": int_cnd.is_no_vars
            },
        },
        "watched_recommended": {
            RESPONSE: 'Ok! And have you watched {random_series2recommend_2}?',
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {
                "watched_recommended_2": int_cnd.is_yes_vars,
                "not_watched_recommended_2": int_cnd.is_no_vars
            },
        },
        "not_watched_recommended": {
            RESPONSE: "Then I highly recommend it to you! It was released in {random_release}, it has {random_duration}."
                    " And here is the desription: {random_description}",
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_ACHIEVED)
            },
        },
        "watched_recommended_2": {
            RESPONSE: "Wow! Ok, let's try one more time. What about {random_series2recommend_3}? Have you watched it?",
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {
                "watched_recommended_3": int_cnd.is_yes_vars,
                "not_watched_recommended_3": int_cnd.is_no_vars
            },
        },
        "not_watched_recommended_2": {
            RESPONSE: "Then I highly recommend it to you! It was released in {random_release_2}, it has {random_duration_2}."
                    " And here is the desription: {random_description_2}",
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_ACHIEVED)
            },
        },
        "watched_recommended_3": {
            RESPONSE: "Oh, I'm afraid you watched all series I know... I give up!",
            PROCESSING: {
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_NOT_ACHIEVED)
            },
        },
        "not_watched_recommended_3": {
            RESPONSE: "Then I highly recommend it to you! It was released in {random_release_3}, it has {random_duration_3}."
                    " And here is the desription: {random_description_3}",
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_ACHIEVED)
            },
        },
    },
    "mentions_known_series": {
        LOCAL: {
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(1.0),
                "set_can_continue": int_prs.set_can_continue(),
                "extract_series2recommend": loc_prs.extract_known_series(),
                "extract_random_series2recommend": loc_prs.extract_random_series2recommend()
            },
        },
        "suggest2recommend": {
            RESPONSE: 'I love this series! And I can recommend you another one. Do you want me to?',
            PROCESSING: {
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_OFFERED)
            },
            TRANSITIONS: {
                "recommend_series": int_cnd.is_yes_vars
            }
        },
        "recommend_series": {
            RESPONSE: 'I higly recommend {recommend_series}. Have you watched it?',
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {
                "watched_recommended": int_cnd.is_yes_vars,
                "not_watched_recommended": int_cnd.is_no_vars
            },
        },
        "watched_recommended": {
            RESPONSE: 'Ok! And have you watched {random_series2recommend_2}?',
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {
                ("recommend_series", "watched_recommended_2"): int_cnd.is_yes_vars,
                ("recommend_series", "not_watched_recommended_2"): int_cnd.is_no_vars
            },
        },
        "not_watched_recommended": {
            RESPONSE: "Then I highly recommend it to you! It was released in {recommend_release}, it has {recommend_duration}."
                    " And here is the desription: {recommend_description}",
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_ACHIEVED)
            },
        },
    },
    "mentions_netflix": {
        LOCAL: {
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(1.0),
                "set_can_continue": int_prs.set_can_continue(),
                "extract_random_series2recommend": loc_prs.extract_random_series2recommend()
            },
        },
        "ask_last_series": {
            RESPONSE: "Speaking of Netflix, what was the last Netflix series you've watched?",
            PROCESSING: {
                "extract_series2recommend": loc_prs.extract_known_series()
            },
            TRANSITIONS: {
                ("mentions_known_series", "suggest2recommend"): cnd.true()
            }
        }
    },
}


actor = Actor(flows, start_label=("sevice", "start"), fallback_label=("sevice", "fallback"))
