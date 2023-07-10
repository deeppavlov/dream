import logging

from df_engine.core.keywords import (
    TRANSITIONS,
    GLOBAL,
    RESPONSE,
)
from df_engine.core import Actor
from . import condition as loc_cnd
from . import response as loc_rsp

logger = logging.getLogger(__name__)

flows = {
    "global_flow": {
        "start": {
            RESPONSE: loc_rsp.generic_response,
            TRANSITIONS: {},
        },
        "fallback": {
            RESPONSE: "Nice picture!",
            TRANSITIONS: {},
        },
    },
}

actor = Actor(
    flows,
    start_label=("global_flow", "start"),
    fallback_label=("global_flow", "fallback"),
)

logger.info("Actor created successfully")
