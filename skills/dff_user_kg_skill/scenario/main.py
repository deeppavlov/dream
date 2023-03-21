import logging
import re
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

import common.constants as common_constants
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
            ("personal_info_flow", "pet_tell_more", 2): int_cnd.has_entities("kg:animal"),
            ("personal_info_flow", "pet_q", 1): cnd.regexp(re.compile(r"(pet|pets)")),
            ("personal_info_flow", "hobby_q", 1): cnd.regexp(re.compile(r"(hobby|hobbies)")),
        }
    },
    "personal_info_flow": {
        "pet_q": {
            RESPONSE: "Do you have a pet?",
            TRANSITIONS: {
                ("personal_info_flow", "pet_r", 2): int_cnd.has_entities("prop:have_pet"),
                ("personal_info_flow", "hobby_q", 1): cnd.true()
            },
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(1.0),
                "set_can_continue": int_prs.set_can_continue(common_constants.MUST_CONTINUE),
            }
        },
        "pet_r": {
            RESPONSE: "Cool! I also have a {users_pet}.",
            TRANSITIONS: {lbl.forward(): cnd.true()},
            PROCESSING: {
                "entity_extraction": int_prs.entities(users_pet=["prop:have_pet", "default:pet"]),
                "slot_filling": int_prs.fill_responses_by_slots(),
                "set_confidence": int_prs.set_confidence(1.0),
                "set_can_continue": int_prs.set_can_continue(common_constants.MUST_CONTINUE),
            },
        },
        "hobby_q": {
            RESPONSE: "Do you have a hobby?",
            TRANSITIONS: {
                ("personal_info_flow", "hobby_r", 2): int_cnd.has_entities("prop:like_activity"),
            },
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(1.0),
                "set_can_continue": int_prs.set_can_continue(common_constants.MUST_CONTINUE),
            },
        },
        "hobby_r": {
            RESPONSE: "Cool! I also like {users_hobby}.",
            TRANSITIONS: {
                ("personal_info_flow", "pet_q", 1): cnd.regexp(re.compile(r"(pet|pets)")),
                lbl.forward(): cnd.true()
            },
            PROCESSING: {
                "entity_extraction": int_prs.entities(users_hobby=["prop:like_activity", "default:this activity"]),
                "slot_filling": int_prs.fill_responses_by_slots(),
                "set_confidence": int_prs.set_confidence(1.0),
                "set_can_continue": int_prs.set_can_continue(common_constants.MUST_CONTINUE),
            },
        },
        "pet_tell_more": {
            RESPONSE: "Tell me more about your {users_pet}.",
            PROCESSING: {
                "slot_filling": int_prs.fill_responses_by_slots(),
                "set_confidence": int_prs.set_confidence(1.0),
                "set_can_continue": int_prs.set_can_continue(common_constants.MUST_CONTINUE),
            },
            TRANSITIONS: {},
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
