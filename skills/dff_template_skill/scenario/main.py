import logging
import re

from dff.script import (
    Message,
    LOCAL,
    PRE_TRANSITIONS_PROCESSING,
    PRE_RESPONSE_PROCESSING,
    TRANSITIONS,
    RESPONSE,
    GLOBAL,
)
import dff.script.conditions as cnd
import dff.script.labels as lbl
from dff.pipeline import Pipeline

import common.dff_api_v1.integration.condition as int_cnd
import common.dff_api_v1.integration.processing as int_prs
import common.dff_api_v1.integration.response as int_rsp


import common.constants as common_constants

from . import condition as loc_cnd
from . import response as loc_rsp

logger = logging.getLogger(__name__)

# First of all, to create a dialog agent, we need to create a dialog script.
# Below, `flows` is the dialog script.
# A dialog script is a flow dictionary that can contain multiple flows .
# Flows are needed in order to divide a dialog into sub-dialogs and process them separately.
# For example, the separation can be tied to the topic of the dialog.
# In our example, there is one flow called greeting_flow.

# Inside each flow, we can describe a sub-dialog using keyword `GRAPH` from df_engine.core.keywords module.
# Here we can also use keyword `GLOBAL_TRANSITIONS`, which we have considered in other examples.

# A flow describes a sub-dialog using linked nodes, each node has the keywords `RESPONSE` and `TRANSITIONS`.

# `RESPONSE` - contains the response that the dialog agent will return when transitioning to this node.
# `TRANSITIONS` - describes transitions from the current node to other nodes.
# `TRANSITIONS` are described in pairs:
#      - the node to which the agent will perform the transition
#      - the condition under which to make the transition

script = {
    GLOBAL: {
        TRANSITIONS: {
            ("greeting", "node1"): cnd.regexp(r"\bhi\b"),
        },
    },
    "service": {
        "start": {
            RESPONSE: Message(text=""),
            TRANSITIONS: {("greeting", "node1"): cnd.true()},
        },
        "fallback": {
            RESPONSE: Message(text="Ooops"),
            TRANSITIONS: {
                lbl.previous(): cnd.regexp(r"previous", re.IGNORECASE),
                lbl.repeat(0.2): cnd.true(),
            },
        },
    },
    "greeting": {
        LOCAL: {
            PRE_RESPONSE_PROCESSING: {
                "set_confidence": int_prs.set_confidence(1.0),
                "set_can_continue": int_prs.set_can_continue(),
                # "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
            },
        },
        "node1": {
            RESPONSE: int_rsp.multi_response(["Hi, how are you?", "Hi, what's up?"]),  # several hypotheses
            PRE_RESPONSE_PROCESSING: {
                "save_slots_to_ctx": int_prs.save_slots_to_ctx({"topic": "science", "user_name": "Gordon Freeman"})
            },
            TRANSITIONS: {"node2": cnd.regexp(r"how are you", re.IGNORECASE)},
        },
        "node2": {
            RESPONSE: loc_rsp.example_response(Message(text="Good. What do you want to talk about?")),
            # loc_rsp.example_response is just for an example, you can use just str without example_response func
            TRANSITIONS: {"node3": loc_cnd.example_lets_talk_about()},
        },
        "node3": {
            RESPONSE: Message(text="Sorry, I can not talk about that now. Maybe late. Do you like {topic}?"),
            PRE_RESPONSE_PROCESSING: {"fill_responses_by_slots": int_prs.fill_responses_by_slots()},
            TRANSITIONS: {
                "node4": int_cnd.is_yes_vars,
                "node5": int_cnd.is_no_vars,
                "node6": int_cnd.is_do_not_know_vars,
                "node7": cnd.true(),  # it will be chosen if other conditions are False
            },
        },
        "node4": {
            RESPONSE: Message(text="I like {topic} too, {user_name}"),
            PRE_RESPONSE_PROCESSING: {"fill_responses_by_slots": int_prs.fill_responses_by_slots()},
            TRANSITIONS: {("node7", 0.1): cnd.true()},
        },
        "node5": {
            RESPONSE: Message(text="I do not like {topic} too, {user_name}"),
            PRE_RESPONSE_PROCESSING: {"fill_responses_by_slots": int_prs.fill_responses_by_slots()},
            TRANSITIONS: {("node7", 0.1): cnd.true()},
        },
        "node6": {
            RESPONSE: Message(text="I have no opinion about {topic} too, {user_name}"),
            PRE_RESPONSE_PROCESSING: {"fill_responses_by_slots": int_prs.fill_responses_by_slots()},
            TRANSITIONS: {("node7", 0.1): cnd.true()},
        },
        "node7": {
            RESPONSE: int_rsp.multi_response(
                replies=["bye", "goodbye"],
                confidences=[1.0, 0.5],
                hype_attr=[
                    {"can_continue": common_constants.MUST_CONTINUE},  # for the first hyp
                    {"can_continue": common_constants.CAN_CONTINUE_SCENARIO},  # for the second hyp
                ],
            ),
            PRE_TRANSITIONS_PROCESSING: {"set_confidence": int_prs.set_confidence(0.0)},
        },
    },
}


db = dict()
pipeline = Pipeline.from_script(
    script=script,
    start_label=("service", "start"),
    fallback_label=("service", "fallback"),
    context_storage=db,
)
