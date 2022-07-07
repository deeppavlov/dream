import common.universal_templates as templates
from common.speech_functions.generic_responses import (
    sys_response_to_speech_function_request as generic_responses_intent,
)
from common.dialogflow_framework.extensions import (
    intents,
    providers,
    custom,
    custom_functions,
    priorities,
    generic_responses,
)
from common.dialogflow_framework.stdm.key_words import (
    TRANSITIONS,
    GLOBAL_TRANSITIONS,
    GRAPH,
    RESPONSE,
    PROCESSING,
    forward,
    previous,
)


flows = {
    "art": {
        GLOBAL_TRANSITIONS: custom.art_to_states,
        GRAPH: {
            "drawing_q": {
                RESPONSE: "Do you like drawing?",
                TRANSITIONS: {
                    ("drawing", "what_painter", priorities.middle): [
                        any,
                        [
                            intents.yes_intent,
                            templates.LIKE_PATTERN,
                            custom_functions.speech_functions("Sustain.Continue.Prolong.Extend"),
                        ],
                    ],
                    forward: intents.always_true,
                },
            },
            "photo_q": {
                RESPONSE: ["Do you like taking photos?", "Do you like photography?"],
                TRANSITIONS: {("photo", "what_photos"): [any, [intents.yes_intent, templates.LIKE_PATTERN]]},
            },
        },
    },
    "drawing": {
        GLOBAL_TRANSITIONS: {
            "what_painter": custom_functions.drawing_request,
        },
        GRAPH: {
            "what_painter": {RESPONSE: "Pictures of what painters do you like?", forward: intents.always_true},
            "what_paintings": {
                RESPONSE: "I also like pictures of {user_fav_painter}. What kind of paintings do you like to draw: "
                "landscapes, portraits or something else?",
                PROCESSING: [
                    custom_functions.entities(user_fav_painter="wiki:Q1028181"),
                    custom_functions.slot_filling,
                ],
                forward: intents.always_true,
            },
            "how_to_draw": {
                RESPONSE: custom_functions.how_to_draw_response,
                TRANSITIONS: {("facts", "how_to_draw"): intents.yes_intent},
            },
        },
    },
    "photo": {
        GRAPH: {
            "what_photos": {
                RESPONSE: "Cool! Do you have any funny photos of your family or pets?",
                TRANSITIONS: {"how_photo": intents.yes_intent},
            },
            "how_photo": {RESPONSE: "Do you take photos on an SLR camera or on your cell phone?"},
        }
    },
    "facts": {
        GLOBAL_TRANSITIONS: {"how_to_draw": intents.facts},
        GRAPH: {
            "how_to_draw": {
                RESPONSE: providers.fact_provider("wikiHow", "Improve-Your-Drawing-Skills"),
                TRANSITIONS: {"how_to_draw": intents.facts},
            }
        },
    },
    "generic_responses_default": generic_responses.create_new_flow(priority=0.9),
    "globals": {
        GLOBAL_TRANSITIONS: {
            ("not_understand", priorities.high): r"i did not understand",
            ("generic_responses_default", "root", priorities.high): generic_responses_intent,
        },
        GRAPH: {
            "not_understand": {RESPONSE: "Sorry for not being clear", TRANSITIONS: {previous: intents.always_true}}
        },
    },
}
