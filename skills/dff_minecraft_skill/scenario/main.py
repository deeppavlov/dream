import logging
import re

from df_engine.core.keywords import LOCAL, PROCESSING, TRANSITIONS, RESPONSE, GLOBAL
from df_engine.core import Context, Actor
import df_engine.conditions as cnd
import df_engine.labels as lbl
from .processing import GO_TO_COMPILED_PATTERN

import common.dff.integration.condition as int_cnd
import common.dff.integration.processing as int_prs
import common.dff.integration.response as int_rsp
import common.minecraft.core.serializer as serializer


import common.constants as common_constants

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
    GLOBAL: {PROCESSING: {1: loc_prs.add_prefix("l1_global"), 2: loc_prs.add_prefix("l2_global")}},
    "service": {
        "start": {
            RESPONSE: "",
            TRANSITIONS: {
                ("commands", "start"): cnd.true()
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
    "commands": {
        "start": {
            PROCESSING: {
                1: loc_prs.add_prefix("l1_start"),
            },
            RESPONSE: "Type your command please", 
            TRANSITIONS: {
                "goto": cnd.regexp(r"(go to)|(move to)|(come to) (\d+)\,*\s*(\d+)\,*\s*(\d+)", re.IGNORECASE),
            },
        },
        "goto": {
            PROCESSING: {
                1: loc_prs.add_prefix("l1_go_to"),
                "get_dest": loc_prs.get_destination(), # заполняем слоты нужными значениями
                "fill_responses_by_slots": int_prs.fill_responses_by_slots() # вставляем слоты в ответ
                },
            RESPONSE: "Okay, I'll go to {dest1}",
            TRANSITIONS: {},
        },
        "test": {
            RESPONSE: "ttt",
            TRANSITIONS: {},
        }
    },
}


actor = Actor(flows, start_label=("service", "start"), fallback_label=("service", "fallback"))
