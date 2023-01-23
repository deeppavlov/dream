import logging
import re
import sentry_sdk
from os import getenv
import random

import df_engine.conditions as cnd
import df_engine.labels as lbl
from df_engine.core.keywords import (
    PROCESSING,
    TRANSITIONS,
    GLOBAL,
    RESPONSE,
    LOCAL,
    MISC
)

import scenario.sf_conditions as dm_cnd

from df_engine.core import Actor

import common.dff.integration.condition as int_cnd
import common.dff.integration.processing as int_prs
import scenario.condition as loc_cnd
import scenario.processing as loc_prs
from . import response as loc_rsp
from common.constants import CAN_CONTINUE_SCENARIO, MUST_CONTINUE, CAN_NOT_CONTINUE

import common.dff.integration.response as int_rsp


sentry_sdk.init(getenv("SENTRY_DSN"))

logger = logging.getLogger(__name__)

SUPER_CONFIDENCE = 1.0
HIGH_CONFIDENCE = 0.98
DEFAULT_CONFIDENCE = 0.95
BIT_LOWER_CONFIDENCE = 0.90
ZERO_CONFIDENCE = 0.0

flows = {
    GLOBAL: {
        TRANSITIONS: {
            ("travel_italy_general", "italy_start", 2): loc_cnd.start_condition,
            ("travel_italy_general", "italy_start", 1): cnd.all(     
                [
                    loc_cnd.is_proposed_skill,
                    cnd.neg(loc_cnd.check_flag("italy_travel_skill_active")),
                ]
            ),
        },
    },
    "travel_italy_general": {
        LOCAL: {
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(SUPER_CONFIDENCE),
                "set_can_continue": int_prs.set_can_continue(MUST_CONTINUE)
            },
        },
        "italy_start": {
            # RESPONSE: "Do you like Italy anna?",
            RESPONSE: "What's your favourite place in Italy?",
            # TRANSITIONS: {
            #     ("travel_italy_general", "not_been_to_italy", 2): int_cnd.is_no_vars,
            #     ("travel_italy_general", "like_italy", 1): cnd.true(),
            # },
            TRANSITIONS: {
                ("travel_italy_general", "fav_place", 2): int_cnd.has_entities("prop:favorite_place"),
                ("travel_italy_general", "like_italy", 1): cnd.true(),
            },
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(SUPER_CONFIDENCE),
                "set_can_continue": int_prs.set_can_continue(MUST_CONTINUE),
                "set_flag": loc_prs.set_flag("italy_travel_skill_active", True),
            },
        },
        "fav_place": {
            RESPONSE: "What are the odds? I also love {users_fav_place}.",
            TRANSITIONS: {
                ("travel_italy_general", "like_italy"): cnd.true(),
            },
            PROCESSING: {
                "entity_extraction": int_prs.entities(
                    users_fav_place=["prop:favorite_place","wiki:Q515", "default:this place"]
                ),
                "slot_filling": int_prs.fill_responses_by_slots(),
                "set_confidence": int_prs.set_confidence(1.0),
                "set_can_continue": int_prs.set_can_continue(MUST_CONTINUE),
            },
        },
        "like_italy": {
            RESPONSE: "Me, too. I like Italy for its nature. What do you like it for?",
            TRANSITIONS: {
                ("travel_italy_general", "told_why", 2): cnd.any(
                    [
                        dm_cnd.is_midas("open_question_opinion"),
                        dm_cnd.is_midas("opinion")
                    ]
                ),
                ("global_flow", "fallback", 1): int_cnd.is_no_vars,
                ("travel_italy_general", "been_to_italy", 1): cnd.true(),
            },
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(SUPER_CONFIDENCE),
                "set_can_continue": int_prs.set_can_continue(MUST_CONTINUE),
                "set_flag": loc_prs.set_flag("italy_travel_skill_active", True),
            },
        },
        "told_why": {
            RESPONSE: int_rsp.multi_response(
                replies=["I think in Italy one can truly relax and taste the life", 
                "Italy is the place where I want to go back again and again."],
                confidences=[1.0, 1.0],
                hype_attr=[
                    {"can_continue": MUST_CONTINUE},
                    {"can_continue": CAN_CONTINUE_SCENARIO},
                ],
            ),
            TRANSITIONS: {("travel_italy_general", "been_to_italy", 2): cnd.true()},
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(SUPER_CONFIDENCE),
                "set_can_continue": int_prs.set_can_continue(MUST_CONTINUE),
            },
            MISC: {"dialog_act": ["opinion"]},
        }, 
        "been_to_italy": { 
            RESPONSE: "Have you ever been to Italy?",
            TRANSITIONS: {
                ("travel_italy_general", "when_visited"): int_cnd.is_yes_vars,
                ("travel_italy_general", "not_been_to_italy"): int_cnd.is_no_vars,
            },
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(SUPER_CONFIDENCE),
                "set_can_continue": int_prs.set_can_continue(MUST_CONTINUE),
            },
        },
        "when_visited": {
            RESPONSE: loc_rsp.append_unused(
                initial="My favourite time to visit Italy is summer. ",
                phrases=[loc_rsp.WHEN_TRAVEL],
            ),
            TRANSITIONS: {("travel_italy_general", "who_with"): cnd.true()},
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(SUPER_CONFIDENCE),
                "set_can_continue": int_prs.set_can_continue(MUST_CONTINUE),
            },
        },
        "who_with": {
            RESPONSE: loc_rsp.append_unused(
                initial="Awesome! ",
                phrases=[loc_rsp.WHO_TRAVEL_WITH],
            ),
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(SUPER_CONFIDENCE),
                "set_can_continue": int_prs.set_can_continue(MUST_CONTINUE),
            },
            TRANSITIONS: {
                ("travel_italy_general", "told_who"): cnd.any(
                    [
                        dm_cnd.is_midas("statement"),
                        dm_cnd.is_midas("opinion")
                    ]
                ),
                ("travel_italy_general", "been_places"): cnd.true(),
            },
        },
        "told_who": {
            RESPONSE: int_rsp.multi_response(
                replies=["It doesn't matter whether you travel to Italy alone or in company. It's fun at all times.", 
                "In Italy you can find fun things to do both alone and in company."],
                confidences=[1.0, 1.0],
                hype_attr=[
                    {"can_continue": MUST_CONTINUE},
                    {"can_continue": CAN_CONTINUE_SCENARIO},
                ],
            ),
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(SUPER_CONFIDENCE),
                "set_can_continue": int_prs.set_can_continue(MUST_CONTINUE),
            },
            TRANSITIONS: {("travel_italy_general", "been_places"): cnd.true()},
            MISC: {"dialog_act": ["opinion"]},
        },
        "been_places": {
            RESPONSE: 'I love this country. I travelled in Italy a lot and everything is beautiful about it. What city '
            'did you visit in Italy?',
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(SUPER_CONFIDENCE),
                "set_can_continue": int_prs.set_can_continue(MUST_CONTINUE),
            }, 
            TRANSITIONS: {
                ("travel_italy_general", "not_been_to_italy"): int_cnd.is_no_vars,
                ("concrete_place_flow", "ask_fav"): cnd.true(),
            }, 
        },
        "not_been_to_italy": {
            RESPONSE: 'What a pity! This country and its culture are truly inspiring. What about italian cuisine? Do you like it?',
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(SUPER_CONFIDENCE),
                "set_can_continue": int_prs.set_can_continue(MUST_CONTINUE),
            },
            TRANSITIONS: {("italian_food_flow", "food_start"): cnd.true()}, 
        },
    },
    "concrete_place_flow": {
        "ask_fav": {
            RESPONSE: "Wow! I visited {user_fav_city}, too. What impressed you the most there?",
            PROCESSING: {
                "entity_extraction": int_prs.entities(
                    user_fav_city=["wiki:Q515", "tag:location", "default:your favourite city"]
                ),
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_confidence": int_prs.set_confidence(SUPER_CONFIDENCE),
                "set_can_continue": int_prs.set_can_continue(MUST_CONTINUE),
            },
            TRANSITIONS: {("concrete_place_flow", "day_activities"): cnd.true()},
        },
        "day_activities": {
            RESPONSE: loc_rsp.append_unused(
                initial="Oh, I loved that, too! ",
                phrases=[loc_rsp.WHAT_DID_DAY],
            ),
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(SUPER_CONFIDENCE),
                "set_can_continue": int_prs.set_can_continue(MUST_CONTINUE),
            },
            TRANSITIONS: {
                ("concrete_place_flow", "bot_activ_opinion"): loc_cnd.sentiment_detected("negative"),
                "night_activities": cnd.true(),
            },
        },
        "night_activities": {
            RESPONSE: "Sounds like you had much fun! How about your nights?",
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(SUPER_CONFIDENCE),
                "set_can_continue": int_prs.set_can_continue(MUST_CONTINUE),
            },
            TRANSITIONS: {("concrete_place_flow", "bot_activ_opinion"): cnd.true()},
        },
        "bot_activ_opinion": {
            RESPONSE: int_rsp.multi_response(
                replies=["I prefer daytime activities: walking around the city, enjoying sun on a bench in some picturesque place... "
                "and sample hundreds of tastes of italian gelato.", 
                "I find it difficult to enjoy wandering about the city when the weather is bad. "
                "If this is the case, I use this time to savour italian specialties in cozy trattorias."],
                confidences=[1.0, 1.0],
                hype_attr=[
                    {"can_continue": MUST_CONTINUE},
                    {"can_continue": CAN_CONTINUE_SCENARIO},
                ],
            ),
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(SUPER_CONFIDENCE),
                "set_can_continue": int_prs.set_can_continue(MUST_CONTINUE),
            },
            TRANSITIONS: {("italian_food_flow", "food_start"): cnd.true()},
            MISC: {"dialog_act": ["opinion"]},
        },
    },
    "italian_food_flow": {
        "food_start": { 
            RESPONSE: "In Italy it's always a nosh-up. Do you agree?",
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(SUPER_CONFIDENCE),
                "set_can_continue": int_prs.set_can_continue(MUST_CONTINUE),
            },
            TRANSITIONS: {("global_flow", "fallback"): cnd.true()},
        },
    },
    "global_flow": {
        "start": {
            RESPONSE: "",
            TRANSITIONS: {},
        },
        "fallback": {
            RESPONSE: "Anyway, let's talk about something else!",
            TRANSITIONS: {},
        },
    },
}


actor = Actor(
    flows, 
    start_label=("global_flow", "start"), 
    fallback_label=("global_flow", "fallback"),
)

logger.info("Actor created successfully")