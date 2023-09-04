import logging
import sentry_sdk
from os import getenv

import df_engine.conditions as cnd
from df_engine.core.keywords import PROCESSING, TRANSITIONS, GLOBAL, RESPONSE, LOCAL, MISC

import scenario.sf_conditions as dm_cnd

from df_engine.core import Actor

import common.dff.integration.condition as int_cnd
import common.dff.integration.processing as int_prs
import scenario.condition as loc_cnd
import scenario.processing as loc_prs
from . import response as loc_rsp
from common.constants import CAN_CONTINUE_SCENARIO, MUST_CONTINUE

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
            ("travel_italy_general", "italy_start"): loc_cnd.start_condition,
            ("travel_italy_general", "like_italy"): loc_cnd.is_proposed_skill,
            ("italian_food_flow_restart", "tell_more"): cnd.all(
                [
                    loc_cnd.has_entity_in_graph("LIKE FOOD/Food"),
                    loc_cnd.uttr_about_favorite_food,
                ]
            ),
            ("italian_food_flow", "food_start"): cnd.all(
                [
                    loc_cnd.asked_about_italian_cuisine,
                    cnd.neg(loc_cnd.check_flag("food_start_visited")),
                ]
            ),
        },
    },
    "travel_italy_general": {
        LOCAL: {
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(SUPER_CONFIDENCE),
                "set_can_continue": int_prs.set_can_continue(MUST_CONTINUE),
            },
        },
        "italy_start": {
            RESPONSE: "What's your favourite place in Italy?",
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(SUPER_CONFIDENCE),
                "set_can_continue": int_prs.set_can_continue(MUST_CONTINUE),
                "set_flag": loc_prs.set_flag("italy_travel_skill_active", True),
            },
            TRANSITIONS: {
                ("concrete_place_flow", "fav_place", 2): cnd.any(
                    [
                        int_cnd.has_entities("wiki:Q747074"),  # Q38 - Italy, Q747074 - commune of Italy
                        int_cnd.has_entities("wiki:Q515"),  # Q515 - city
                        int_cnd.has_entities("wiki:Q1549591"),  # Q1549591 - big city
                    ]
                ),
                ("travel_italy_general", "like_italy", 1): cnd.true(),
            },
        },
        "like_italy": {
            RESPONSE: "I like Italy for its nature. What do you like it for?",
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(BIT_LOWER_CONFIDENCE),
                "set_can_continue": int_prs.set_can_continue(CAN_CONTINUE_SCENARIO),
                "set_flag": loc_prs.set_flag("italy_travel_skill_active", True),
            },
            TRANSITIONS: {
                ("travel_italy_general", "told_why", 2): cnd.any(
                    [dm_cnd.is_midas("open_question_opinion"), dm_cnd.is_midas("opinion")]
                ),
                ("travel_italy_general", "neg_to_italy"): int_cnd.is_no_vars,
                ("global_flow", "fallback"): cnd.true(),
            },
        },
        "told_why": {
            RESPONSE: int_rsp.multi_response(
                replies=[
                    "I think in Italy one can truly relax and taste the life",
                    "Italy is the place where I want to go back again and again.",
                ],
                confidences=[1.0, 1.0],
                hype_attr=[
                    {"can_continue": MUST_CONTINUE},
                    {"can_continue": CAN_CONTINUE_SCENARIO},
                ],
            ),
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(BIT_LOWER_CONFIDENCE),
                "set_can_continue": int_prs.set_can_continue(CAN_CONTINUE_SCENARIO),
            },
            TRANSITIONS: {
                ("concrete_place_flow", "when_visited"): cnd.true(),
            },
        },
        "neg_to_italy": {
            RESPONSE: "What a pity! This country and its culture are truly inspiring. What about italian cuisine? "
            "Do you like it?",
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(DEFAULT_CONFIDENCE),
                "set_can_continue": int_prs.set_can_continue(MUST_CONTINUE),
            },
            TRANSITIONS: {
                ("italian_food_flow", "food_start"): int_cnd.is_yes_vars,
                ("global_flow", "fallback"): cnd.true(),
            },
        },
    },
    "concrete_place_flow": {
        "fav_place": {
            RESPONSE: "What are the odds? I also love {users_fav_place}. What impressed you the most there?",
            PROCESSING: {
                "entity_extraction": int_prs.entities(users_fav_place=["prop:favorite_place", "default:this place"]),
                "slot_filling": int_prs.fill_responses_by_slots(),
                "set_confidence": int_prs.set_confidence(SUPER_CONFIDENCE),
                "set_can_continue": int_prs.set_can_continue(MUST_CONTINUE),
            },
            TRANSITIONS: {
                ("concrete_place_flow", "when_visited"): int_cnd.is_no_vars,
                ("concrete_place_flow", "day_activities"): cnd.true(),
            },
        },
        "day_activities": {
            RESPONSE: loc_rsp.append_unused(
                initial="Oh, I loved that, too! ",
                phrases=[loc_rsp.WHAT_DID_DAY],
            ),
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(HIGH_CONFIDENCE),
                "set_can_continue": int_prs.set_can_continue(MUST_CONTINUE),
            },
            TRANSITIONS: {
                ("concrete_place_flow", "like_activity", 2): cnd.any(
                    [int_cnd.has_entities("prop:like_activity"), int_cnd.has_entities("prop:favorite_activity")]
                ),
                ("concrete_place_flow", "bot_activ_opinion"): int_cnd.is_no_vars,
                ("concrete_place_flow", "when_visited"): cnd.true(),
            },
        },
        "like_activity": {
            RESPONSE: "{user_liked_activity} is one of the things I like to do as well. What about your nights?",
            PROCESSING: {
                "entity_extraction": int_prs.entities(user_liked_activity=["prop:like_activity", "default:This"]),
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_confidence": int_prs.set_confidence(DEFAULT_CONFIDENCE),
                "set_can_continue": int_prs.set_can_continue(MUST_CONTINUE),
            },
            TRANSITIONS: {("concrete_place_flow", "bot_activ_opinion"): cnd.true()},
        },
        "bot_activ_opinion": {
            RESPONSE: int_rsp.multi_response(
                replies=[
                    "I prefer daytime activities: walking around the city, enjoying sun on a bench in some "
                    "picturesque place... and sample hundreds of tastes of italian gelato.",
                    "I find it difficult to enjoy wandering about the city when the weather is bad. "
                    "If this is the case, I use this time to savour italian specialties in cozy trattorias.",
                ],
                confidences=[1.0, 1.0],
                hype_attr=[
                    {"can_continue": MUST_CONTINUE},
                    {"can_continue": CAN_CONTINUE_SCENARIO},
                ],
            ),
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(DEFAULT_CONFIDENCE),
                "set_can_continue": int_prs.set_can_continue(CAN_CONTINUE_SCENARIO),
            },
            TRANSITIONS: {("concrete_place_flow", "when_visited"): cnd.true()},
            MISC: {"dialog_act": ["opinion"]},
        },
        "when_visited": {
            RESPONSE: loc_rsp.append_unused(
                initial="My favourite time to visit Italy is summer. ",
                phrases=[loc_rsp.WHEN_TRAVEL],
            ),
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(BIT_LOWER_CONFIDENCE),
                "set_can_continue": int_prs.set_can_continue(CAN_CONTINUE_SCENARIO),
            },
            TRANSITIONS: {
                ("concrete_place_flow", "told_when", 2): cnd.any(
                    [int_cnd.has_entities("prop:favorite_season"), int_cnd.has_entities("prop:like_season")]
                ),
                ("italian_food_flow", "food_start"): cnd.true(),
            },
        },
        "told_when": {
            RESPONSE: "It's fun at all seasons but especially in {user_fav_season}.",
            PROCESSING: {
                "entity_extraction": int_prs.entities(user_fav_season=["prop:favorite_season", "default:this time"]),
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_confidence": int_prs.set_confidence(BIT_LOWER_CONFIDENCE),
                "set_can_continue": int_prs.set_can_continue(CAN_CONTINUE_SCENARIO),
            },
            TRANSITIONS: {("italian_food_flow", "food_start"): cnd.true()},
        },
    },
    "italian_food_flow": {
        "food_start": {
            RESPONSE: "In Italy it's always a nosh-up. Is there any italian dish that you never get tired of eating?",
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(SUPER_CONFIDENCE),
                "set_can_continue": int_prs.set_can_continue(MUST_CONTINUE),
                "set_flag": loc_prs.set_flag("food_start_visited", True),
            },
            TRANSITIONS: {
                ("italian_food_flow", "fav_food"): cnd.any(
                    [int_cnd.has_entities("prop:like_food"), int_cnd.has_entities("prop:favorite_food")]
                ),
                ("italy_disappointments", "neg_experience"): cnd.true(),
            },
        },
        "fav_food": {
            RESPONSE: "Oh, {user_like_food} is to-die-for. What drink does it go best with?",
            PROCESSING: {
                "entity_extraction": int_prs.entities(user_like_food=["prop:like_food", "default:this dish"]),
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_can_continue": int_prs.set_can_continue(MUST_CONTINUE),
                "set_confidence": int_prs.set_confidence(DEFAULT_CONFIDENCE),
            },
            TRANSITIONS: {
                ("italian_food_flow", "fav_drink"): cnd.any(
                    [int_cnd.has_entities("prop:favorite_drink"), int_cnd.has_entities("prop:like_drink")]
                ),
                ("italy_disappointments", "neg_experience"): cnd.true(),
            },
        },
        "fav_drink": {
            RESPONSE: "It is a useful recommendation. I'll try {user_like_drink} next time. Thank you!",
            PROCESSING: {
                "entity_extraction": int_prs.entities(user_like_drink=["prop:like_drink", "default:this pairing"]),
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_can_continue": int_prs.set_can_continue(MUST_CONTINUE),
                "set_confidence": int_prs.set_confidence(BIT_LOWER_CONFIDENCE),
            },
            TRANSITIONS: {
                ("italy_disappointments", "neg_experience"): cnd.true(),
            },
        },
    },
    "italian_food_flow_restart": {
        "tell_more": {
            RESPONSE: "Aha, so was it {LIKE FOOD}? If so, where and how did you first try it?",
            PROCESSING: {
                "fill_responses_by_slots": loc_prs.fill_responses_by_slots_from_graph(),
                "set_confidence": int_prs.set_confidence(HIGH_CONFIDENCE),
            },
            TRANSITIONS: {
                ("italy_disappointments", "neg_experience"): cnd.true(),
            },
        },
    },
    "italy_disappointments": {
        "neg_experience": {
            RESPONSE: "You know what disappointed me the most in Florence? The parking! "
            "I had to leave the car on the outskirts of the city. Was there anything you disliked in Italy?",
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(BIT_LOWER_CONFIDENCE),
                "set_can_continue": int_prs.set_can_continue(CAN_CONTINUE_SCENARIO),
            },
            TRANSITIONS: {
                ("italy_disappointments", "sympathy"): int_cnd.has_entities("prop:dislike"),
                ("global_flow", "fallback"): cnd.true(),
            },
        },
        "sympathy": {
            RESPONSE: "I had no idea. I would feel the same way about {user_dislike}.",
            PROCESSING: {
                "entity_extraction": int_prs.entities(user_dislike=["prop:dislike", "default:such situation"]),
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
                "set_confidence": int_prs.set_confidence(DEFAULT_CONFIDENCE),
            },
            TRANSITIONS: {
                ("global_flow", "fallback"): cnd.true(),
            },
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
