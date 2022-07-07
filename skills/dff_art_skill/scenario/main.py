import logging
import sentry_sdk
from os import getenv

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
import scenario.condition as loc_cnd
import scenario.processing as loc_prs
import common.universal_templates as templates
from common.art import SUPER_CONFIDENCE, HIGH_CONFIDENCE

sentry_sdk.init(getenv("SENTRY_DSN"))

logger = logging.getLogger(__name__)

flows = {
    GLOBAL: {
        TRANSITIONS: {
            ("art", "drawing_q", 2): cnd.all(
                [loc_cnd.art_skill_switch, cnd.neg(loc_cnd.check_flag("art_skill_active"))]
            ),
            ("art", "photo_q", 1): cnd.all([loc_cnd.art_skill_switch, cnd.neg(loc_cnd.check_flag("art_skill_active"))]),
        }
    },
    "art": {
        "drawing_q": {
            RESPONSE: "Do you like drawing?",
            TRANSITIONS: {
                ("drawing", "what_painter", 2): cnd.any(
                    [
                        int_cnd.is_yes_vars,
                        cnd.regexp(templates.LIKE_PATTERN),
                    ],
                ),
                lbl.forward(): cnd.true(),
            },
            PROCESSING: {
                "set_flag": loc_prs.set_flag("art_skill_active"),
                "set_confidence": loc_prs.set_start_confidence,
            },
        },
        "photo_q": {
            RESPONSE: ["Do you like taking photos?"],
            TRANSITIONS: {("photo", "what_photos"): cnd.any([int_cnd.is_yes_vars, cnd.regexp(templates.LIKE_PATTERN)])},
            PROCESSING: {
                "set_flag": loc_prs.set_flag("art_skill_active"),
                "set_confidence": int_prs.set_confidence(SUPER_CONFIDENCE),
            },
        },
    },
    "drawing": {
        "what_painter": {
            RESPONSE: "Pictures of what painters do you like?",
            TRANSITIONS: {lbl.forward(): cnd.true()},
            PROCESSING: {"set_confidence": int_prs.set_confidence(HIGH_CONFIDENCE)},
        },
        "what_paintings": {
            RESPONSE: "I also like pictures of {user_fav_painter}. What kind of paintings do you like to draw: "
            "landscapes, portraits or something else?",
            PROCESSING: {
                "entity_extraction": int_prs.entities(
                    user_fav_painter=["wiki:Q1028181", "tag:person", "default:your favourite painter"]
                ),
                "slot_filling": int_prs.fill_responses_by_slots(),
            },
            TRANSITIONS: {lbl.forward(): cnd.true()},
        },
        "how_to_draw": {
            RESPONSE: "Would you like to know how to improve your drawing skills?",
            TRANSITIONS: {("facts", "how_to_draw"): int_cnd.is_yes_vars},
        },
    },
    "photo": {
        "what_photos": {
            RESPONSE: "Cool! Do you have any funny photos of your family or pets?",
            TRANSITIONS: {"how_photo": int_cnd.is_yes_vars},
        },
        "how_photo": {
            RESPONSE: "Do you take photos on an SLR camera or on your cell phone?",
            TRANSITIONS: {("global_flow", "fallback"): cnd.true()},
        },
    },
    "facts": {
        "how_to_draw": {
            RESPONSE: "",
            PROCESSING: {
                "wikihow": int_prs.fact_provider("wikiHow", "Improve-Your-Drawing-Skills"),
            },
            TRANSITIONS: {lbl.forward(): int_cnd.facts},
        }
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
