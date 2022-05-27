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

from common.get_book_recommendation import BOOKS_PATTERN, APPRECIATION_PATTERN, GENRES_PATTERN, BOOKS_TOPIC_PATTERN, RECOMMEND_BOOK_PATTERN, RECOMMEND_PATTERN
from common.constants import GOAL_DETECTED, GOAL_IN_PROGRESS, GOAL_ACHIEVED, GOAL_NOT_ACHIEVED, GOAL_OFFERED

import common.set_goal_flag as goal_status

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
            ("book_by_genre", "genre_q"): cnd.all([cnd.regexp(BOOKS_PATTERN), cnd.regexp(APPRECIATION_PATTERN)]),
            ("book_by_genre", "fan_of_genre2"): cnd.all([cnd.regexp(GENRES_PATTERN), cnd.regexp(APPRECIATION_PATTERN)]),
            ("book_by_genre", "q_book_by_genre"): cnd.all([cnd.regexp(RECOMMEND_PATTERN), cnd.regexp(GENRES_PATTERN)]),
            ("book_by_genre", "q_fav_genre"): cnd.regexp(RECOMMEND_BOOK_PATTERN), 
            ("book_by_genre", "offer_recommend_book"): cnd.regexp(BOOKS_TOPIC_PATTERN)
        },
    },
    "sevice": {
        "start": {
            RESPONSE: "",
            TRANSITIONS: {
                # ("book_by_genre", "genre_q"): cnd.true()
                ("book_by_genre", "genre_q"): cnd.all([cnd.regexp(BOOKS_PATTERN), cnd.regexp(APPRECIATION_PATTERN)]),
                ("book_by_genre", "fan_of_genre2"): cnd.all([cnd.regexp(GENRES_PATTERN), cnd.regexp(APPRECIATION_PATTERN)]),
                ("book_by_genre", "q_book_by_genre"): cnd.all([cnd.regexp(RECOMMEND_PATTERN), cnd.regexp(GENRES_PATTERN)]),
                ("book_by_genre", "q_fav_genre"): cnd.regexp(RECOMMEND_BOOK_PATTERN),
                ("book_by_genre", "offer_recommend_book"): cnd.regexp(BOOKS_TOPIC_PATTERN)
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
    "book_by_genre": {
        LOCAL: {
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(2.0),
                "set_can_continue": int_prs.set_can_continue(),
                "extract_book_genre": loc_prs.extract_book_genre(),
                "extract_fav_genre": loc_prs.extract_fav_genre()
            },
        },
        "offer_recommend_book": {
            RESPONSE: "Sure! I believe that I can recommend you one. Do you want me to?",
            PROCESSING: {
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_OFFERED)
            },
            TRANSITIONS: {
                "q_fav_genre_2": int_cnd.is_yes_vars,
            }
        },
        "genre_q": {
            RESPONSE: "So you're a fan of {fav_book_genre} book genre, aren't you?",  
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {"recommend_book_by_genre": cnd.any([int_cnd.is_yes_vars, int_cnd.is_do_not_know_vars])},
        },
        "fan_of_genre": {
            RESPONSE: "What {fav_book_genre} novels have you read?",
            PROCESSING: {
                 "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                 "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {"recommend_book_by_genre": cnd.true()},
        },
         "recommend_book_by_genre": {
            RESPONSE: "Oh, then you should read {book_recommend}",
            PROCESSING: {
                 "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                 "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_ACHIEVED)
                },
        },
        "fan_of_genre2": {
            RESPONSE: "What {fav_genre} novels have you read?",
            PROCESSING: {
                 "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                 "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
            TRANSITIONS: {"recommend_book_by_genre": cnd.true()},
        },
        "q_book_by_genre": {
            RESPONSE: "Have you read {book_recommend_1}?",
            PROCESSING:  {
                 "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                 "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
                },
            TRANSITIONS: {
                "already_read": int_cnd.is_yes_vars,
                "suggest2read": int_cnd.is_no_vars
            },
        },
        "q_fav_genre": {
            RESPONSE: "What is your favorite genre?",
            TRANSITIONS: {
                "q_book_by_genre": cnd.regexp(GENRES_PATTERN)
            },
            PROCESSING: {
                "extract_fav_genre": loc_prs.extract_fav_genre(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            }
        },
        "q_fav_genre_2": {
            RESPONSE: "Great! What is your favorite genre?",
            TRANSITIONS: {
                "q_book_by_genre": cnd.regexp(GENRES_PATTERN)
            },
            PROCESSING: {
                "extract_fav_genre": loc_prs.extract_fav_genre(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            }
        },
        "already_read": {
            RESPONSE: "Ok! And what about {book_recommend_2}? Have you read it?",
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
             TRANSITIONS: {
                "already_read_2": int_cnd.is_yes_vars,
                "suggest2read": int_cnd.is_no_vars
            }, 
        },
        "already_read_2": {
            RESPONSE: "Hmmm... let's take a last chance! Have you read {book_recommend_3}?",
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_IN_PROGRESS)
            },
             TRANSITIONS: {
                "already_read_3": int_cnd.is_yes_vars,
                "suggest2read": int_cnd.is_no_vars
            }, 
        },
        "already_read_3": {
            RESPONSE: "I really don't know what to recommend you then& But I'll learn!",
            PROCESSING: {
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_NOT_ACHIEVED)
            }
        },
        "suggest2read": {
            RESPONSE: "You should read it! This is an amazing book. The plot is breathtaking, and I really liked the characters!",
            PROCESSING: {
                "set_goal_status_flag": goal_status.set_goal_status_flag(GOAL_ACHIEVED)
            }
        }
    },
}


actor = Actor(flows, start_label=("sevice", "start"), fallback_label=("sevice", "fallback"))