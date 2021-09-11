import logging

from dff.core.keywords import TRANSITIONS, GRAPH, RESPONSE
from dff.core import Actor
import dff.conditions as cnd

from . import response as loc_rsp

logger = logging.getLogger(__name__)

flows = {
    "story_flow": {
        GRAPH: {
            "start_node": {
                RESPONSE: loc_rsp.programy_reponse,
                TRANSITIONS: {
                    "start_node": cnd.true,
                },
            },
        }
    }
}

actor = Actor(flows, start_node_label=("story_flow", "start_node"))
