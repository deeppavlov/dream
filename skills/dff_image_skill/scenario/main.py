import logging
import df_engine.conditions as cnd
import df_engine.labels as lbl

from df_engine.core.keywords import (
    PROCESSING,
    TRANSITIONS,
    GLOBAL,
    RESPONSE,
)
from df_engine.core import Actor
import common.dff.integration.condition as int_cnd
import common.dff.integration.processing as int_prs
from . import condition as loc_cnd
from . import response as loc_rsp
import scenario.processing as loc_prs
import common.universal_templates as templates

logger = logging.getLogger(__name__)

flows = {
    GLOBAL: {
        TRANSITIONS: {
            ("caption_response", "animals_node"): loc_cnd.detect_animals_on_caption_condition,
            ("caption_response", "food_node"): loc_cnd.detect_food_on_caption_condition,
            ("caption_response", "people_node"): loc_cnd.detect_people_on_caption_condition,
            ("caption_response", "general_node"): loc_cnd.detect_other_on_caption_condition,
        }
    },
    "caption_response": {
        "animals_node": {
            RESPONSE: loc_rsp.animals_response,
            TRANSITIONS: {},
        },
        "food_node": {
            RESPONSE: loc_rsp.food_response,
            TRANSITIONS: {},
        },
        "people_node": {
            RESPONSE: loc_rsp.people_response,
            TRANSITIONS: {},
        },
        "general_node": {
            RESPONSE: loc_rsp.generic_response,
            TRANSITIONS: {},
        },
    },   
    "global_flow": {
        "start": {
            RESPONSE: "",
            TRANSITIONS: {},
        },
        "fallback": {
            RESPONSE: 'Nice picture!',
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
