import logging

from dff.core.keywords import TRANSITIONS, GRAPH, RESPONSE
from dff.core import Actor
import dff.conditions as cnd
import dff.transitions as trn

import common.dff.integration.condition as int_cnd

from . import condition as loc_cnd
from . import response as loc_rsp

logger = logging.getLogger(__name__)

flows = {
    "story_flow": {
        GRAPH: {
            "start_node": {
                RESPONSE: "",
                TRANSITIONS: {
                    "choose_story_node": cnd.all([loc_cnd.is_tell_me_a_story, loc_rsp.get_story_type, loc_rsp.get_story_left]),
                    "which_story_node": cnd.all([loc_cnd.is_tell_me_a_story, cnd.neg(loc_rsp.get_story_type)]),
                    "fallback_node": cnd.true,
                },
            },

            "choose_story_node": {
                RESPONSE: loc_rsp.choose_story_response,
                TRANSITIONS: {     
                    "tell_punchline_node": cnd.any([int_cnd.is_yes_vars, int_cnd.is_do_not_know_vars]),
                    "which_story_node": int_cnd.is_no_vars,
                    "fallback_node": cnd.true,
                },
            },

            "which_story_node": {
                RESPONSE: loc_rsp.which_story_response,
                TRANSITIONS: {
                    "choose_story_node": cnd.all([loc_rsp.get_story_type, loc_rsp.get_story_left]),
                    "fallback_node": cnd.true,
                },
            },
            
            "tell_punchline_node": {
                RESPONSE: loc_rsp.tell_punchline_response,
                TRANSITIONS: {
                    "fallback_node": cnd.true,
                    },
            },
            "fallback_node": {
                RESPONSE: loc_rsp.fallback_response,
                TRANSITIONS:{
                    "which_story_node": cnd.all([loc_cnd.is_asked_for_a_story, int_cnd.is_yes_vars]),
                    trn.repeat(): cnd.true,
                }
            },
        }
    }
}

actor = Actor(flows, start_node_label=("story_flow", "start_node"), fallback_node_label=("story_flow", "fallback_node"))
