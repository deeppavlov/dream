import logging

import common.dff.integration.condition as int_cnd
import common.dff.integration.context as int_ctx
import common.dff.integration.processing as int_prs
import df_engine.labels as lbl
import df_engine.conditions as cnd
import scenario.condition as loc_cnd
import scenario.processing as loc_prs
import scenario.response as loc_rsp
from common.constants import CAN_CONTINUE_SCENARIO, MUST_CONTINUE, CAN_NOT_CONTINUE
from df_engine.core.keywords import RESPONSE, TRANSITIONS, PROCESSING, TRANSITIONS, GLOBAL, RESPONSE, MISC
from df_engine.core import Actor

from .responses import greeting_response


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

logger = logging.getLogger(__name__)
ZERO_CONFIDENCE = 0.0

flows = {
    "global_flow": {
        "start": {
            RESPONSE: "",
            PROCESSING: {"set_can_continue": int_prs.set_can_continue(MUST_CONTINUE)},
            TRANSITIONS: {("greeting", "greeting_start"): cnd.true()},
        },
        "fallback": {
            RESPONSE: "",
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(ZERO_CONFIDENCE),
                "set_can_continue": int_prs.set_can_continue(CAN_NOT_CONTINUE),
            },
            TRANSITIONS: {},
        },
    },
    "greeting": {
        "start_node": {
            RESPONSE: "",
            TRANSITIONS: {"greeting_response_node": cnd.true()},
        },
        "greeting_response_node": {
            RESPONSE: greeting_response,
            TRANSITIONS: {lbl.repeat(): cnd.true()},
        },
    },
}

actor = Actor(
    flows,
    start_label=("global_flow", "start"),
    fallback_label=("global_flow", "fallback"),
)
logger.info("Actor created successfully")
