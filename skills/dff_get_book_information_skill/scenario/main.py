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
from common.get_book_information import TELL_ABOUT_BOOK_PATTERN, TELL_BOOK_GENRE_PATTERN, TELL_BOOK_AUTHOR_PATTERN, TELL_BOOK_DESCRIPTION_PATTERN

import common.set_goal_flag as goal_status
from common.constants import GOAL_DETECTED, GOAL_IN_PROGRESS, GOAL_ACHIEVED, GOAL_NOT_ACHIEVED, GOAL_OFFERED

from . import condition as loc_cnd
from . import response as loc_rsp
from . import processing as loc_psr

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
            ("tell_about", "give_info"): cnd.regexp(TELL_ABOUT_BOOK_PATTERN),
            ("tell_about", "genres"): cnd.regexp(TELL_BOOK_GENRE_PATTERN),
            ("tell_about", "author") : cnd.regexp(TELL_BOOK_AUTHOR_PATTERN),
            ("tell_about", "description") : cnd.regexp(TELL_BOOK_DESCRIPTION_PATTERN)
        },
    },
    "sevice": {
        "start": {
            RESPONSE: "",
            TRANSITIONS: {
                ("tell_about", "give_info"): cnd.regexp(TELL_ABOUT_BOOK_PATTERN),
                ("tell_about", "genres"): cnd.regexp(TELL_BOOK_GENRE_PATTERN),
                ("tell_about", "author") : cnd.regexp(TELL_BOOK_AUTHOR_PATTERN),
                ("tell_about", "description") : cnd.regexp(TELL_BOOK_DESCRIPTION_PATTERN)
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
    "tell_about": {
        LOCAL: {
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(1.0),
                "set_can_continue": int_prs.set_can_continue(),
                "extract_book": loc_psr.extract_book()
            },
        },
        "give_info": {
            RESPONSE: "It's {genres} written by {author}, and it's rating is {rating}. "
                    "And here is the description: {description}",
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_ACHIEVED)
            }
        },
        "genres": {
            RESPONSE: "It's {genres}",
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_ACHIEVED)
            }
        },
        "author": {
            RESPONSE: "The author of this book is {author}",
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_ACHIEVED)
            }
        },
        "description": {
            RESPONSE: "Here is the book's description: {description}",
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_ACHIEVED)
            }
        }
    },
}


actor = Actor(flows, start_label=("sevice", "start"), fallback_label=("sevice", "fallback"))
