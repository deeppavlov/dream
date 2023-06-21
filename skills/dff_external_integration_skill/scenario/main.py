import logging

from df_engine.core.keywords import TRANSITIONS, RESPONSE, LOCAL, PROCESSING
from df_engine.core import Actor
import df_engine.conditions as cnd
import df_engine.labels as lbl

import common.dff.integration.processing as int_prs

from . import response as loc_rsp

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

logger = logging.getLogger(__name__)

flows = {
    "external_response": {
        LOCAL: {PROCESSING: {"set_confidence": int_prs.set_confidence(1.0)}},
        "start_node": {
            RESPONSE: "",
            TRANSITIONS: {"external_response_node": cnd.true()},
        },
        "external_response_node": {
            RESPONSE: loc_rsp.get_external_skill_response,
            TRANSITIONS: {lbl.repeat(): cnd.true()},
        },
    },
}

actor = Actor(
    flows,
    start_label=("external_response", "start_node"),
    fallback_node_label=("external_response", "external_response_node"),
)
