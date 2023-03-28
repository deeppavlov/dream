import logging
import re
import sentry_sdk
from os import getenv
import random
# from deeppavlov_kg import TerminusdbKnowledgeGraph

from df_engine.core.keywords import LOCAL, PROCESSING, TRANSITIONS, RESPONSE, GLOBAL
from df_engine.core import Actor
import df_engine.conditions as cnd
import df_engine.labels as lbl

import common.dff.integration.condition as int_cnd
import common.dff.integration.processing as int_prs
import common.dff.integration.response as int_rsp
from . import condition as loc_cnd
import scenario.processing as loc_prs
from . import response as loc_rsp
from common.constants import CAN_CONTINUE_SCENARIO, MUST_CONTINUE, CAN_NOT_CONTINUE

sentry_sdk.init(getenv("SENTRY_DSN"))

logger = logging.getLogger(__name__)



flows = {
    GLOBAL: {
        TRANSITIONS: {
            ("bakery_general", "bakery_start"): loc_cnd.start_condition,
        },
    },
    "bakery_general": {
        LOCAL: {
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(1.0),
                "set_can_continue": int_prs.set_can_continue(),
            },
        },
        "bakery_start": {
            RESPONSE: "Our bakery is happy to help! What would you like to know?", 
            TRANSITIONS: {
                ("bakery_general","dessert_ingredients"): loc_cnd.has_entity_in_graph(),
                ("global_flow", "fallback"): cnd.true(),
            },
        },
        "dessert_ingredients": {
            RESPONSE: "Excellent choice! {dessert_name} consists of {ingredients}.",  # dessert (Q182940)
            # PROCESSING: {
            #     "fill_responses_by_slots": loc_prs.fill_responses_by_slots_from_graph(),
            # },
            TRANSITIONS: {("global_flow", "fallback"): loc_cnd.example_lets_talk_about()},
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
