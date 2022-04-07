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

from common.get_book_recommendation import BOOKS_PATTERN, APPRECIATION_PATTERN, GENRES_PATTERN

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
            ("book_by_genre", "q_book_by_genre"): cnd.all([cnd.regexp(r"recommend", re.IGNORECASE), cnd.regexp(GENRES_PATTERN)]),
            ("book_by_genre", "q_fav_genre"): cnd.all([cnd.regexp(r"recommend", re.IGNORECASE), cnd.regexp(r"book", re.IGNORECASE)]) # не отрабатывает
        },
    },
    "sevice": {
        "start": {
            RESPONSE: "",
            TRANSITIONS: {
                # ("book_by_genre", "genre_q"): cnd.true()
                ("book_by_genre", "genre_q"): cnd.all([cnd.regexp(BOOKS_PATTERN), cnd.regexp(APPRECIATION_PATTERN)]),
                ("book_by_genre", "fan_of_genre2"): cnd.all([cnd.regexp(GENRES_PATTERN), cnd.regexp(APPRECIATION_PATTERN)]),
                ("book_by_genre", "q_book_by_genre"): cnd.all([cnd.regexp(r"recommend", re.IGNORECASE), cnd.regexp(GENRES_PATTERN)]),
                ("book_by_genre", "q_fav_genre"): cnd.all([cnd.regexp(r"recommend", re.IGNORECASE), cnd.regexp(r"book", re.IGNORECASE)])
                },
        },
        "fallback": {
            RESPONSE: "Ooops",
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
        "genre_q": {
            RESPONSE: "So you're a fan of {fav_book_genre} novels, aren't you?",  
            PROCESSING: {
                "fill_responses_by_slots": int_prs.fill_responses_by_slots()
            },
            TRANSITIONS: {"fan_of_genre": cnd.any([int_cnd.is_yes_vars, int_cnd.is_do_not_know_vars])},
        },
        "fan_of_genre": {
            RESPONSE: "What {fav_book_genre} novels have you read?",
            PROCESSING: {
                 "fill_responses_by_slots": int_prs.fill_responses_by_slots()
            },
            TRANSITIONS: {"recommend_book_by_genre": cnd.true()},
        },
         "recommend_book_by_genre": {
            RESPONSE: "Oh, then you should read {book_recommend}",
            PROCESSING: {
                 "fill_responses_by_slots": int_prs.fill_responses_by_slots()
                },
        },
        "fan_of_genre2": {
            RESPONSE: "What {fav_genre} novels have you read?",
            PROCESSING: {
                 "fill_responses_by_slots": int_prs.fill_responses_by_slots()
            },
            TRANSITIONS: {"recommend_book_by_genre": cnd.true()},
        },
        "q_book_by_genre": {
            RESPONSE: "Have you read {book_recommend} ?",
            PROCESSING:  {
                 "fill_responses_by_slots": int_prs.fill_responses_by_slots()
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
                "extract_fav_genre": loc_prs.extract_fav_genre()
            }
        },
        "already_read": {
            RESPONSE: "Did you like it?",
        },
        "suggest2read": {
            RESPONSE: "You should read it! I really liked the plot and the characters!"
        }
    },
}


actor = Actor(flows, start_label=("sevice", "start"), fallback_label=("sevice", "fallback"))