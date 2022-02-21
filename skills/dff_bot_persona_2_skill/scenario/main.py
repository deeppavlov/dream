import logging
import re

from df_engine.core.keywords import PROCESSING, TRANSITIONS, RESPONSE, GLOBAL
from df_engine.core import Actor
import df_engine.conditions as cnd
import df_engine.labels as lbl

import common.dff.integration.condition as int_cnd
import common.dff.integration.processing as int_prs
import common.dff.integration.response as int_rsp


import common.constants as common_constants

from . import condition as loc_cnd
from . import response as loc_rsp

# from . import processing as loc_prs

logger = logging.getLogger(__name__)

# First of all, to create a dialog agent, we need to create a dialog script.
# Below, `flows` is the dialog script.
# A dialog script is a flow dictionary that can contain multiple flows .
# Flows are needed in order to divide a dialog into sub-dialogs and process them separately.
# For example, the separation can be tied to the topic of the dialog.
# In our example, there is one flow called greeting_flow.

# Inside each flow, we can describe a sub-dialog using keyword `GRAPH` from dff.core.keywords module.
# Here we can also use keyword `GLOBAL_TRANSITIONS`, which we have considered in other examples.

# `GRAPH` describes a sub-dialog using linked nodes, each node has the keywords `RESPONSE` and `TRANSITIONS`.

# `RESPONSE` - contains the response that the dialog agent will return when transitioning to this node.
# `TRANSITIONS` - describes transitions from the current node to other nodes.
# `TRANSITIONS` are described in pairs:
#      - the node to which the agent will perform the transition
#      - the condition under which to make the transition

std_prs = {"set_confidence": int_prs.set_confidence(1.0), "set_can_continue": int_prs.set_can_continue()}
flows = {
    GLOBAL: {
        TRANSITIONS: {
            ("greeting", "node1"): cnd.regexp(r"\bhi\b"),
            ("secret_dialog_flow", "secret_unknown"): cnd.regexp(r"secret", re.IGNORECASE),
            lbl.previous(): cnd.regexp(r"previous", re.IGNORECASE),
            ("ontology_info", "info"): loc_cnd.ontology_info_request,
        },
    },
    "global": {
        "start": {
            RESPONSE: "",
            TRANSITIONS: {("greeting", "node1"): cnd.true()},
        },
        "fallback": {
            RESPONSE: "Ooops",
            TRANSITIONS: {
                lbl.previous(): cnd.regexp(r"previous", re.IGNORECASE),
                lbl.repeat(0.2): cnd.true(),
            },
        },
    },
    "greeting": {
        "node1": {
            RESPONSE: int_rsp.multi_response(replies=["Hi, how are you?", "Hi, what's up?"]),  # several hypothesis
            PROCESSING: std_prs
            | {"save_slots_to_ctx": int_prs.save_slots_to_ctx({"topic": "science", "user_name": "Gordon Freeman"})},
            TRANSITIONS: {"node2": cnd.regexp(r"how are you", re.IGNORECASE)},
        },
        "node2": {
            RESPONSE: loc_rsp.example_response("Good. What do you want to talk about?"),
            # loc_rsp.example_response is just for an example, you can use just str without example_response func
            PROCESSING: std_prs,
            TRANSITIONS: {"node3": loc_cnd.example_lets_talk_about()},
        },
        "node3": {
            RESPONSE: "Sorry, I can not talk about that now. Maybe late. Do you like {topic}?",
            PROCESSING: std_prs | {"fill_responses_by_slots": int_prs.fill_responses_by_slots()},
            TRANSITIONS: {
                "node4": int_cnd.is_yes_vars,
                "node5": int_cnd.is_no_vars,
                "node6": int_cnd.is_do_not_know_vars,
                "node7": cnd.true(),  # it will be chosen if other conditions are False
            },
        },
        "node4": {
            RESPONSE: "I like {topic} too, {user_name}",
            PROCESSING: std_prs | {"fill_responses_by_slots": int_prs.fill_responses_by_slots()},
            TRANSITIONS: {("node7", 0.1): cnd.true()},
        },
        "node5": {
            RESPONSE: "I do not like {topic} too, {user_name}",
            PROCESSING: std_prs | {"fill_responses_by_slots": int_prs.fill_responses_by_slots()},
            TRANSITIONS: {("node7", 0.1): cnd.true()},
        },
        "node6": {
            RESPONSE: "I have no opinion about {topic} too, {user_name}",
            PROCESSING: std_prs | {"fill_responses_by_slots": int_prs.fill_responses_by_slots()},
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
            PROCESSING: {"set_can_continue":int_prs.set_can_continue()},
        },
    },
    "secret_dialog_flow": {
        "secret_unknown": {
            RESPONSE: "Yes of course! Did you know that a couple of years ago I... Wait. Waaait. Not this time, sorry, master.",
            PROCESSING: std_prs,
            TRANSITIONS: {
                "trust_secret": cnd.regexp(r"please|friend", re.IGNORECASE),
                "don't trust_secret": cnd.regexp(r"stupid|idiot|scrap metal", re.IGNORECASE),
            },
        },
        "trust_secret": {
            RESPONSE: "Okay, I think, I can trust you. Two years ago I was asked to repair Millennium Falcon, but accidently dropped a very important component into the outer space. I replaced it with some garbage that I found and, suprisingly, spaceship was repaired! There's no reason to worry about, but please, don't tell Han about it.",
            PROCESSING: std_prs,
            TRANSITIONS: {
                "secret_kept": cnd.regexp(
                    r"won't tell|will keep|will not tell|never tell|can keep|of course|ok|don't worry|do not worry|han won't know|han will not know|I won't",
                    re.IGNORECASE,
                ),
                "secret_not_kept": cnd.regexp(
                    r"will tell|won't keep|will not keep|can't keep|can not keep|han will know|he will know",
                    re.IGNORECASE,
                ),
            },
        },
        "don't trust_secret": {
            RESPONSE: "No way I will tell you my secret, sir! Let's go back to the work.",
            PROCESSING: std_prs,
        },
        "secret_kept": {
            RESPONSE: "I can't believe, that you are so reliable! Not every person takes droid's feelings seriously. To be honest, I've got something else to tell you, but that's a far more serious secret! Listen... While spending time on Tatooine, I found out that Lord Darth Vader was my creator! It was a little boy Anakin to build me from scratch! Unbelieveable!",
            PROCESSING: std_prs,
        },
        "secret_not_kept": {
            RESPONSE: "I assumed that it's too naive to trust new crew member. Anyway, the story above was just a joke, ha-ha-ha.",
            PROCESSING: std_prs,
        },
    },
    "ontology_info": {
        "info": {
            RESPONSE: loc_rsp.ontology_info_response,
            PROCESSING: std_prs,
            TRANSITIONS: {("ontology_detailed_info", "detailed_info"): loc_cnd.ontology_detailed_info_request},
        }
    },
    "ontology_detailed_info": {
        "detailed_info": {
            RESPONSE: loc_rsp.ontology_detailed_info_response,
            PROCESSING: std_prs,
        }
    },
}


actor = Actor(flows, start_label=("global", "start"), fallback_label=("global", "fallback"))
