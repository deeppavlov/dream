import logging

from df_engine.core.keywords import GLOBAL, TRANSITIONS, RESPONSE
from df_engine.core import Actor
import df_engine.conditions as cnd

import common.dff.integration.condition as int_cnd

from . import condition as loc_cnd
from . import response as loc_rsp

logger = logging.getLogger(__name__)

flows = {
    GLOBAL: {TRANSITIONS: {("story_flow", "fallback_node"): cnd.true()}},
    "main_flow": {
        "start_node": {
            RESPONSE: "",
            TRANSITIONS: {
                "ask_name": cnd.true(),
            },
        },
        "process_name": {
            RESPONSE: loc_rsp.find_name,
            TRANSITIONS: {
                "process_name": cnd.true()
            },
        },
        "ask_name": {
            RESPONSE: 'What is your name?',
            TRANSITIONS: {"process_name": cnd.true()},
        },
        "fallback_node": {
            RESPONSE: loc_rsp.fallback,
            TRANSITIONS: {"ask_name": cnd.true()},
        },
    },
}

actor = Actor(flows, start_label=("main_flow", "start_node"), fallback_label=("main_flow", "fallback_node"))
