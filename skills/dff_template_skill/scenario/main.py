import logging

from dff.core.keywords import GRAPH, RESPONSE, PROCESSING, TRANSITIONS
from dff.core import Actor, Context, Node
import dff.transitions as trs

from .conditions import predetermined_condition
from .responses import grounding_response

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

logger = logging.getLogger(__name__)

flows = {
    "grounding": {
        GRAPH: {
            "start_node": {
                RESPONSE: "",
                TRANSITIONS: {"grounding_response_node": predetermined_condition(True)},
            },
            "grounding_response_node": {
                RESPONSE: grounding_response,
                TRANSITIONS: {trs.repeat(): predetermined_condition(True)},
            },
        }
    },
}

actor = Actor(
    flows, start_node_label=("grounding", "start_node"), fallback_node_label=("grounding", "grounding_response_node")
)
