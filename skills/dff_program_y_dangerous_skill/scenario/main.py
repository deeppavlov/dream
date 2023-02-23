import logging

import common.dff.integration.processing as int_prs
import df_engine.conditions as cnd
from common.constants import CAN_NOT_CONTINUE
from df_engine.core.keywords import PROCESSING, TRANSITIONS, RESPONSE
from df_engine.core import Actor

from . import response as loc_rsp


logger = logging.getLogger(__name__)
DEFAULT_CONFIDENCE = 0.9

flows = {
    "story_flow": {
        "start_node": {
            RESPONSE: loc_rsp.programy_reponse,
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(DEFAULT_CONFIDENCE),
                "set_can_continue": int_prs.set_can_continue(CAN_NOT_CONTINUE),
            },
            TRANSITIONS: {
                "start_node": cnd.true(),
            },
        }
    }
}

actor = Actor(flows, start_label=("story_flow", "start_node"))
