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
    "api": {
        LOCAL: {PROCESSING: {"set_confidence": int_prs.set_confidence(1.0)}},
        "start_node": {
            RESPONSE: "",
            TRANSITIONS: {"api_response_node": cnd.true()},
        },
        "api_response_node": {
            RESPONSE: loc_rsp.response_with_chosen_api,
            TRANSITIONS: {lbl.repeat(): cnd.true()},
        }
    },
}

# flows = {
#     "api": {
#         LOCAL: {PROCESSING: {"set_confidence": int_prs.set_confidence(1.0)}},
#         "start_node": {
#             RESPONSE: "",
#             TRANSITIONS: {"google_api_response_node": cnd.true()},
#         },
#         "google_api_response_node": {
#             RESPONSE: loc_rsp.google_api_response,
#             TRANSITIONS: {lbl.repeat(): cnd.true()},
#         },
#         "transformers_lm_response_node:": {
#             RESPONSE: loc_rsp.generative_response,
#             TRANSITIONS: {lbl.repeat(): cnd.true()},
#         },
#         "weather_api_response_node:": {
#             RESPONSE: loc_rsp.weather_api_response,
#             TRANSITIONS: {lbl.repeat(): cnd.true()},
#         }
#     },
# }

actor = Actor(
    flows,
    start_label=("api", "start_node"),
    fallback_node_label=("api", "api_response_node"),
)
