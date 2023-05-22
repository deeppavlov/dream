import logging

from df_engine.core.keywords import TRANSITIONS, RESPONSE
from df_engine.core import Actor
import df_engine.conditions as cnd
import df_engine.labels as lbl

from . import response as loc_rsp
from . import condition as loc_cnd

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

logger = logging.getLogger(__name__)

flows = {
    "generation": {
        "generative_response_node": {
            RESPONSE: loc_rsp.generative_response,
            TRANSITIONS: {
                "updating_prompt_node": loc_cnd.if_updating_prompt,
                "reseting_prompt_node": loc_cnd.if_reseting_prompt,
                lbl.repeat(): cnd.true(),
            },
        },
        "updating_prompt_node": {
            RESPONSE: loc_rsp.updating_prompt_response,
            TRANSITIONS: {
                "generative_response_node": cnd.true(),
            },
        },
        "reseting_prompt_node": {
            RESPONSE: loc_rsp.reseting_prompt_response,
            TRANSITIONS: {
                "generative_response_node": cnd.true(),
            },
        },
    },
}

actor = Actor(flows, start_label=("generation", "generative_response_node"))
