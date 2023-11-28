import logging

from df_engine.core.keywords import TRANSITIONS, RESPONSE
from df_engine.core import Actor
import df_engine.conditions as cnd

from . import response as loc_rsp

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

logger = logging.getLogger(__name__)

flows = {
    "generation": {
        "generative_response_node": {
            RESPONSE: loc_rsp.generative_response,
            TRANSITIONS: {
                "generative_response_node": cnd.true(),
            },
        },
    },
}

actor = Actor(flows, start_label=("generation", "generative_response_node"))
