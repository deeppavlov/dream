import logging

from dff.core.keywords import GLOBAL, TRANSITIONS, RESPONSE
from dff.core import Actor
import dff.conditions as cnd

import common.dff.integration.condition as int_cnd

from . import condition as loc_cnd
from . import response as loc_rsp

logger = logging.getLogger(__name__)

flows = {
    GLOBAL: {TRANSITIONS: {("story_flow", "fallback_node"): cnd.true()}},
    "story_flow": {
        "start_node": {
            RESPONSE: "",
            TRANSITIONS: {
                "choose_story_node": cnd.all(
                    [
                        loc_cnd.is_tell_me_a_story,
                        loc_cnd.has_story_type,
                        loc_cnd.has_story_left,
                    ]
                ),
                "which_story_node": cnd.all([loc_cnd.is_tell_me_a_story, cnd.neg(loc_cnd.has_story_type)]),
            },
        },
        "choose_story_node": {
            RESPONSE: loc_rsp.choose_story,
            TRANSITIONS: {
                "tell_punchline_node": cnd.any([int_cnd.is_yes_vars, int_cnd.is_do_not_know_vars]),
                "which_story_node": int_cnd.is_no_vars,
            },
        },
        "which_story_node": {
            RESPONSE: loc_rsp.which_story,
            TRANSITIONS: {"choose_story_node": cnd.all([loc_cnd.has_story_type, loc_cnd.has_story_left])},
        },
        "tell_punchline_node": {
            RESPONSE: loc_rsp.tell_punchline,
        },
        "fallback_node": {
            RESPONSE: loc_rsp.fallback,
            TRANSITIONS: {"which_story_node": cnd.all([loc_cnd.is_asked_for_a_story, int_cnd.is_yes_vars])},
        },
    },
}

actor = Actor(flows, start_label=("story_flow", "start_node"), fallback_label=("story_flow", "fallback_node"))
