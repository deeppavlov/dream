import logging
import re


import dff.script.conditions as cnd
import dff.script.labels as lbl
from dff.script import (
    MultiMessage,
    LOCAL,
    PRE_TRANSITIONS_PROCESSING,
    PRE_RESPONSE_PROCESSING,
    TRANSITIONS,
    RESPONSE,
    GLOBAL,
)
from dff.pipeline import Pipeline

import common.dff_api_v1.integration.condition as int_cnd
import common.dff_api_v1.integration.processing as int_prs
import common.dff_api_v1.integration.response as int_rsp
from common.dff_api_v1.integration.message import DreamMessage


import common.constants as common_constants

from . import condition as loc_cnd
from . import response as loc_rsp

logger = logging.getLogger(__name__)

# First of all, to create a dialog agent, we need to create a dialog script.
# Below, we lay out our script and assign it to the `script` variable.
# A dialog script is a dictionary each item of which corresponds to a different namespace, aka flow.
# Flows allow you to divide a dialog into sub-dialogs and process them separately.
# For example, the separation can be tied to the topic of the dialog.
# In our example, there is one flow called greeting.

# A flow describes a sub-dialog using linked nodes, each node has the keywords `RESPONSE` and `TRANSITIONS`.

# `RESPONSE` - contains the response that the dialog agent will return when visiting this node.
# `TRANSITIONS` - describes transitions from the current node to other nodes.
# `TRANSITIONS` are described in pairs:
#      - the node to visit
#      - the condition under which to make the transition

script = {
    GLOBAL: {
        TRANSITIONS: {
            ("greeting", "node1"): cnd.regexp(r"\bhi\b"),
        },
    },
    "service": {
        "start": {
            RESPONSE: DreamMessage(text=""),
            # We simulate extraction of two slots at the dialog start.
            # Slot values are then used in the dialog.
            PRE_TRANSITIONS_PROCESSING: {
                "save_slots_to_ctx": int_prs.save_slots_to_ctx({"topic": "science", "user_name": "Gordon Freeman"})
            },
            TRANSITIONS: {("greeting", "node1"): cnd.true()},
        },
        "fallback": {
            RESPONSE: DreamMessage(text="Ooops"),
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
            },
        },
        "node1": {
            RESPONSE: MultiMessage(
                messages=[DreamMessage(text="Hi, how are you?"), DreamMessage(text="Hi, what's up?")]
            ),  # several hypotheses
            TRANSITIONS: {"node2": cnd.regexp(r"how are you", re.IGNORECASE)},
        },
        "node2": {
            # The response section can contain any function that returns a DreamMessage.
            RESPONSE: loc_rsp.example_response(DreamMessage(text="Good. What do you want to talk about?")),
            TRANSITIONS: {"node3": loc_cnd.example_lets_talk_about()},
        },
        "node3": {
            RESPONSE: int_rsp.fill_by_slots(
                DreamMessage(text="Sorry, I can not talk about that now. Maybe later. Do you like {topic}?")
            ),
            TRANSITIONS: {
                "node4": int_cnd.is_yes_vars,
                "node5": int_cnd.is_no_vars,
                "node6": int_cnd.is_do_not_know_vars,
                "node7": cnd.true(),  # this option will be chosen if no other condition is met.
            },
        },
        "node4": {
            # Invoke a special function to insert slots to the response.
            RESPONSE: int_rsp.fill_by_slots(DreamMessage(text="I like {topic} too, {user_name}")),
            TRANSITIONS: {("node7", 0.1): cnd.true()},
        },
        "node5": {
            RESPONSE: int_rsp.fill_by_slots(DreamMessage(text="I do not like {topic} too, {user_name}")),
            TRANSITIONS: {("node7", 0.1): cnd.true()},
        },
        "node6": {
            RESPONSE: int_rsp.fill_by_slots(DreamMessage(text="I have no opinion about {topic} too, {user_name}")),
            TRANSITIONS: {("node7", 0.1): cnd.true()},
        },
        "node7": {
            RESPONSE: MultiMessage(
                # DreamMessage attributes, like confidence and can_continue status
                # can be used to override the parameters extracted by Dream engine.
                messages=[
                    DreamMessage(
                        text="bye", confidence=1.0, hype_attr={"can_continue": common_constants.MUST_CONTINUE}
                    ),
                    DreamMessage(
                        text="goodbye",
                        confidence=0.5,
                        hype_attr={"can_continue": common_constants.CAN_CONTINUE_SCENARIO},
                    ),
                ]
            ),
            PRE_RESPONSE_PROCESSING: {"set_confidence": int_prs.set_confidence(0.0)},
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
