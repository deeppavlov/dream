import logging
import re

from df_engine.core.keywords import LOCAL, PROCESSING, TRANSITIONS, RESPONSE, GLOBAL
from df_engine.core import Actor, Context
import df_engine.conditions as cnd
import df_engine.labels as lbl

import common.dff.integration.condition as int_cnd
import common.dff.integration.processing as int_prs
import common.dff.integration.response as int_rsp
import common.dff.integration.context as int_ctx

import common.utils as common_utils
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

THANK_PATTERN = re.compile(r"thanks|thank you|(I'll|I will) (try|watch|read|cook|think)|okay|good|great", re.IGNORECASE)


flows = {
    GLOBAL: {
        TRANSITIONS: {
            ("recommend", "ask_for_details"): cnd.regexp(r"recommend", re.IGNORECASE),
        },
    },
    "sevice": {
        "start": {
            RESPONSE: "",
            TRANSITIONS: {("recommend", "begin"): cnd.true()},
        },
        "fallback": {
            RESPONSE: "Ooops",
            TRANSITIONS: {
                lbl.previous(): cnd.regexp(r"previous", re.IGNORECASE),
                lbl.repeat(0.2): cnd.true(),
            },
        },
    },
    "recommend": {
        LOCAL: {
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(1.0),
                "set_can_continue": int_prs.set_can_continue(),
                # "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
            },
        },
        "begin": {
            RESPONSE: "I'm here to recommend you something nice.",  # several hypothesis
            TRANSITIONS: {"ask_for_details": cnd.true()
            },
        },
        "ask_for_details": {
            RESPONSE: int_rsp.multi_response(replies=["Could you give me some more details on what you want?", 
            "Any details?"]),  # several hypothesis
            TRANSITIONS: {"details_denied": cnd.any(
                [int_cnd.is_no_vars, 
                int_cnd.is_do_not_know_vars],
                ),
                "details_given": cnd.true()
            },
        },
        "details_denied": {
            RESPONSE: loc_rsp.generate_infilling_response('Okay, then I could recommend you my favourite thing, _.'),
            PROCESSING: {
                "save_slots_to_ctx": loc_prs.save_previous_utterance("details")
            },
            # loc_rsp.example_response is just for an example, you can use just str without example_response func
            TRANSITIONS: {
                "answer_question": int_cnd.is_question, 
                "give_opinion": int_cnd.is_opinion_request,
                "user_contented": cnd.regexp(THANK_PATTERN),  # it will be chosen if other conditions are False
                "second_recommendation": cnd.true(),
            },
        },
        "details_given": {
            RESPONSE: loc_rsp.generate_infilling_response(prompts=['Then I would recommend you _.', 'Then my recommendation is _.']),
            PROCESSING: {
                "save_slots_to_ctx": loc_prs.save_previous_utterance("details")
            },
            TRANSITIONS: {
                "answer_question": int_cnd.is_question, 
                "give_opinion": int_cnd.is_opinion_request,
                "user_contented": cnd.regexp(THANK_PATTERN),  # it will be chosen if other conditions are False
                "second_recommendation": cnd.true(),
            },
        },
        "answer_question": {
            RESPONSE: loc_rsp.generate_infilling_response(prompts=["I'm not sure, but _.", "As far as I know, _.", '_.']),
            TRANSITIONS: {
                "answer_question": int_cnd.is_question, 
                "give_opinion": int_cnd.is_opinion_request,
                "user_contented": cnd.regexp(THANK_PATTERN),
                "ask_for_approval": cnd.true()
                },
        },
        "give_opinion": {
            RESPONSE: loc_rsp.generate_infilling_response(prompts=['I think that _.', 'Well, I would say that _.', 'In my opinion, _']),
            TRANSITIONS: {
                "answer_question": int_cnd.is_question, 
                "give_opinion": int_cnd.is_opinion_request,
                "user_contented": cnd.regexp(THANK_PATTERN),
                "ask_for_approval": cnd.true()
                },
        },
        "ask_for_approval": {
            RESPONSE: int_rsp.multi_response(replies=["So what do you think about my recommendation?", 
            "Do you like my suggestion?"]),
            TRANSITIONS: {
                "user_contented": cnd.any(
                [int_cnd.is_no_vars, 
                int_cnd.is_do_not_know_vars,
                loc_cnd.is_negative_sentiment
                ],
                ),
                "finish": cnd.true()
                },
        },
        "user_contented": {
            RESPONSE: "Happy to help. Do you want another recommendation from me?",
            TRANSITIONS: {
                "second_recommendation": int_cnd.is_yes_vars,
                "finish": cnd.true()
                },
        },
        "second_recommendation": {
            RESPONSE: loc_rsp.generate_infilling_response(['Apart from that, I could recommend you _.', 'Then I would also recommend you _.']),
            TRANSITIONS: {"finish": cnd.true()},
        },
        "finish": {
            RESPONSE: "Okay, have fun.",
            TRANSITIONS: {},
        },
    },
}


actor = Actor(flows, start_label=("sevice", "start"), fallback_label=("sevice", "fallback"))