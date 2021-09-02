import logging

import dff.conditions as cnd
import dff.transitions as trn
from dff.core import Actor
from dff.core.keywords import GRAPH, RESPONSE, TRANSITIONS

from .condition import another_funfact_condition, random_funfact_condition, thematic_funfact_condition
from .response import random_funfact_response, thematic_funfact_response

logger = logging.getLogger(__name__)

flows = {
    "global": {
        GRAPH: {
            "start": {
                RESPONSE: "",
                TRANSITIONS: {
                    ("funfact", "thematic"): thematic_funfact_condition,
                    ("funfact", "random"): random_funfact_condition,
                },
            },
            "fallback": {
                RESPONSE: "Ooops",
                TRANSITIONS: {
                    ("funfact", "thematic"): thematic_funfact_condition,
                    ("funfact", "random"): random_funfact_condition,
                },
            },
        },
    },
    "funfact": {
        GRAPH: {
            "random": {
                RESPONSE: random_funfact_response,
                TRANSITIONS: {
                    "thematic": thematic_funfact_condition,
                    trn.repeat(): cnd.any([random_funfact_condition, another_funfact_condition]),
                },
            },
            "thematic": {
                RESPONSE: thematic_funfact_response,
                TRANSITIONS: {
                    trn.repeat(): thematic_funfact_condition,
                    "random": cnd.any([random_funfact_condition, another_funfact_condition]),
                },
            },
        }
    },
}

actor = Actor(flows, start_node_label=("global", "start"), fallback_node_label=("global", "fallback"))
