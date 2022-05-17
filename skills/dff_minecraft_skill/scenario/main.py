import logging
import re

from df_engine.core.keywords import LOCAL, PROCESSING, TRANSITIONS, RESPONSE, GLOBAL
from df_engine.core import Context, Actor
import df_engine.conditions as cnd
import df_engine.labels as lbl

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

def add_prefix(prefix):
    def add_prefix_processing(ctx: Context, actor: Actor, *args, **kwargs) -> Context:
        processed_node = ctx.framework_states["actor"].get("processed_node", ctx.framework_states["actor"]["next_node"])
        processed_node.response = f"{prefix}: {processed_node.response}"
        ctx.framework_states["actor"]["processed_node"] = processed_node
        return ctx
    return add_prefix_processing

flows = {
   # GLOBAL: {
        # TRANSITIONS: {
        #     ("commands", "goto"): cnd.regexp(r"(?:(?:go to)|(?:move to)|(?:come to)) (\d+)\,*\s*(\d+)\,*\s*(\d+)", re.IGNORECASE),
        # },
   # },
    GLOBAL: {
        TRANSITIONS: {
            ("commands", "start"): cnd.regexp(r"\bhi\b", re.IGNORECASE),
        },
    },
    "service": {
        "start": {
            RESPONSE: "",
            TRANSITIONS: {
                ("commands", "start"): cnd.regexp(r"\bhi", re.IGNORECASE)
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
        LOCAL: {
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(1.0),
                "set_can_continue": int_prs.set_can_continue(),
                # "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
            },
        },
        "start": {
            RESPONSE: "Type your command please", 
            # PROCESSING: {
            #     #1: add_prefix("l1_step_1")
            #     #"save_slots_to_ctx": int_prs.save_slots_to_ctx({"dest1": loc_prs.get_destination()
            #     # "encoded_command": serializer.encode_actions({"action": "goto", 
            #     # "args": [loc_prs.get_destination()[0], loc_prs.get_destination()[1], loc_prs.get_destination()[2]],
            #     # "kwargs": {"range_goal": 1}})
            #     #})
            # },
            TRANSITIONS: {
                #"goto": cnd.regexp(r"(?:(?:go to)|(?:move to)|(?:come to)) (\d+)\,*\s*(\d+)\,*\s*(\d+)", re.IGNORECASE)
                ("commands", "goto", 1): cnd.true(),
                "test": cnd.regexp(r"\bok\b", re.IGNORECASE),
            },
        },
        "goto": {
            RESPONSE: "Okay, I'll go",
            # PROCESSING: {
            #     #"fill_responses_by_slots": int_prs.fill_responses_by_slots()
            #     },
            TRANSITIONS: {},
        },
        "test": {
            RESPONSE: "ttt",
            # PROCESSING: {
            #     #"fill_responses_by_slots": int_prs.fill_responses_by_slots()
            #     },
            TRANSITIONS: {},
        }
    },
}


actor = Actor(flows, start_label=("service", "start"), fallback_label=("service", "fallback"))
