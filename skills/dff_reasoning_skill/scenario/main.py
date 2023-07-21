import logging

from df_engine.core.keywords import TRANSITIONS, RESPONSE, PROCESSING
from df_engine.core import Actor
import df_engine.conditions as cnd

import common.dff.integration.condition as int_cnd
import common.dff.integration.processing as int_prs

from . import response as loc_rsp
from . import condition as loc_cnd
from . import processing as loc_prc

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

logger = logging.getLogger(__name__)

flows = {
    "api": {
        "start_node": {
            RESPONSE: "",
            TRANSITIONS: {"plan": cnd.true()},
        },
        "plan": {
            RESPONSE: loc_rsp.plan,
            PROCESSING: {
                "set_is_final_answer_flag": int_prs.set_is_final_answer_flag("false"),
            },
            TRANSITIONS: {"check_if_needs_details": cnd.true()},
        },
        "check_if_needs_details": {
            RESPONSE: loc_rsp.check_if_needs_details,
            PROCESSING: {"set_is_final_answer_flag": int_prs.set_is_final_answer_flag("false")},
            TRANSITIONS: {"clarify_details": loc_cnd.needs_details, "choose_tool": cnd.true()},
        },
        "clarify_details": {
            RESPONSE: loc_rsp.clarify_details,
            PROCESSING: {
                "set_is_final_answer_flag": int_prs.set_is_final_answer_flag("true"),
                "save_user_answer": loc_prc.save_user_answer(),
            },
            TRANSITIONS: {"choose_tool": cnd.true()},
        },
        "choose_tool": {
            RESPONSE: loc_rsp.choose_tool,
            PROCESSING: {
                "set_is_final_answer_flag": int_prs.set_is_final_answer_flag("false"),
            },
            TRANSITIONS: {"ask4approval": loc_cnd.is_tool_needs_approval, "complete_subtask": cnd.true()},
        },
        "ask4approval": {
            RESPONSE: loc_rsp.ask4approval,
            PROCESSING: {
                "set_is_final_answer_flag": int_prs.set_is_final_answer_flag("true"),
            },
            TRANSITIONS: {
                "complete_subtask": cnd.all([loc_cnd.is_last_utt_approval_question, int_cnd.is_yes_vars]),
                "api_usage_not_approved": cnd.all([loc_cnd.is_last_utt_approval_question, int_cnd.is_no_vars]),
            },
        },
        "complete_subtask": {
            RESPONSE: loc_rsp.complete_subtask,
            PROCESSING: {
                "set_is_final_answer_flag": int_prs.set_is_final_answer_flag("false"),
                "save_approves_tool": loc_prc.save_approved_api(),
            },
            TRANSITIONS: {"self_reflexion": cnd.true()},
        },
        "api_usage_not_approved": {
            RESPONSE: "Sorry, I'm afraid I don't know what I can do then.",
            PROCESSING: {"set_is_final_answer_flag": int_prs.set_is_final_answer_flag("true")},
            TRANSITIONS: {},
        },
        "self_reflexion": {
            RESPONSE: loc_rsp.self_reflexion,
            PROCESSING: {"set_is_final_answer_flag": int_prs.set_is_final_answer_flag("false")},
            TRANSITIONS: {
                "check_if_needs_details": cnd.all([loc_cnd.is_self_reflection_ok, cnd.neg(loc_cnd.is_last_step)]),
                "final_response": cnd.all([loc_cnd.is_self_reflection_ok, loc_cnd.is_last_step]),
                "recomplete_task": cnd.all([cnd.neg(loc_cnd.is_self_reflection_ok), loc_cnd.is_tries_left]),
                "revise_plan": cnd.all([cnd.neg(loc_cnd.is_self_reflection_ok), cnd.neg(loc_cnd.is_tries_left)])
            },
        },
        "final_response": {
            RESPONSE: loc_rsp.final_answer,
            PROCESSING: {"set_is_final_answer_flag": int_prs.set_is_final_answer_flag("true")},
            TRANSITIONS: {"plan": cnd.true()},
        },
        "recomplete_task": {
            RESPONSE: loc_rsp.recomplete_task,
            PROCESSING: {
                "set_is_final_answer_flag": int_prs.set_is_final_answer_flag("false"),
                "save_tries": loc_prc.save_tries(),
            },
            TRANSITIONS: {"check_if_needs_details": cnd.true()},
        },
        "revise_plan": {
            RESPONSE: loc_rsp.revise_plan,
            PROCESSING: {
                "set_is_final_answer_flag": int_prs.set_is_final_answer_flag("false"),
            },
            TRANSITIONS: {"check_if_needs_details": cnd.true()},
        },
        "fallback_node": {
            RESPONSE: "Ooops, something went wrong!",
            PROCESSING: {"set_is_final_answer_flag": int_prs.set_is_final_answer_flag("true")},
            TRANSITIONS: {},
        },
    },
}

actor = Actor(
    flows,
    start_label=("api", "start_node"),
    fallback_node_label=("api", "fallback_node"),
)
