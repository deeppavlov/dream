import logging

from df_engine.core.keywords import TRANSITIONS, RESPONSE
from df_engine.core import Actor
import df_engine.conditions as cnd

from . import response as loc_rsp

logger = logging.getLogger(__name__)

flows = {
    "story_flow": {
        "start_node": {
            RESPONSE: loc_rsp.programy_reponse,
            TRANSITIONS: {
                "start_node": cnd.true(),
            },
        }
    }
}

actor = Actor(flows, start_label=("story_flow", "start_node"))
