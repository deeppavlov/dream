import logging

from dff.core.keywords import RESPONSE, TRANSITIONS
from dff.core import Actor
import dff.labels as lbl
import dff.conditions as cnd

from .responses import grounding_response

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

logger = logging.getLogger(__name__)

flows = {
    "grounding": {
        "start_node": {
            RESPONSE: "",
            TRANSITIONS: {"grounding_response_node": cnd.true()},
        },
        "grounding_response_node": {
            RESPONSE: grounding_response,
            TRANSITIONS: {lbl.repeat(): cnd.true()},
        },
    },
}

actor = Actor(
    flows, start_label=("grounding", "start_node"), fallback_node_label=("grounding", "grounding_response_node")
)
