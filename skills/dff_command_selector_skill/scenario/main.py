import logging
import re
import df_engine.conditions as cnd
from df_engine.core import Actor
from df_engine.core.keywords import GLOBAL, PROCESSING, RESPONSE, TRANSITIONS

import scenario.response as rsp
import scenario.condition as loc_cnd
import common.dff.integration.processing as int_prs

logger = logging.getLogger(__name__)

ZERO_CONFIDENCE = 0.0
"""
"Как тебя зовут?"
"Я экспериментальный образец, у меня пока нет имени"
"Кто тебя создал?"
"Меня разработали в центре искусственного интеллекта"
"Что ты умеешь?"
"Моей основной задачей является управление робототехническими комплексами и беспилотным транспортом"
"Как ты работаешь?"
"Я функционирую благодаря комплексной платформе, которая обрабатывает голосовые команды и преобразуют их в действия."
"Чем ты отличаешься от других голосовых ассистентов?"
"Я специализируюсь на управлении робототехническими комплексами и беспилотным транспортом, что делает меня уникальным среди ассистентов"
"""
flows = {
    "service": {
        "start": {RESPONSE: ""},
        "fallback": {RESPONSE: "", PROCESSING: {"set_confidence": int_prs.set_confidence(ZERO_CONFIDENCE)}},
    },
    GLOBAL: {
        TRANSITIONS: {
            ("whatsyourname", "default"): cnd.regexp(r"Как тебя зовут", re.IGNORECASE),
            ("whomadeyou", "default"):   cnd.regexp(r"Кто тебя создал", re.IGNORECASE),
            ("whatcanyoudo", "default"): cnd.regexp(r"Что ты умеешь", re.IGNORECASE),
            ("howdoyouwork", "default"): cnd.regexp(r"Как ты работаешь", re.IGNORECASE),
            ("howareyounew", "default"): cnd.regexp(r"Чем ты отличаешься от других голосовых ассистентов", re.IGNORECASE),
            ("context_driven_response", "command_selector"): loc_cnd.command_selector_exists_condition,
            ("simple", "default"): cnd.true(),
        },
    },
    "context_driven_response": {
        "command_selector": {
            RESPONSE: rsp.command_selector_response,
            PROCESSING: {"set_confidence": rsp.set_confidence_from_input},
        },
    },
    "whatsyourname": {
        "default": {
            RESPONSE: "Я экспериментальный образец, у меня пока нет имени",
            PROCESSING: {"set_confidence": int_prs.set_confidence(1.0)},
        },
    },
    "whomadeyou": {
        "default": {
            RESPONSE: "Меня разработали в центре искусственного интеллекта",
            PROCESSING: {"set_confidence": int_prs.set_confidence(1.0)},
        },
    },
    "whatcanyoudo": {
        "default": {
            RESPONSE: "Моей основной задачей является управление робототехническими комплексами и беспилотным транспортом",
            PROCESSING: {"set_confidence": int_prs.set_confidence(1.0)},
        },
    },
    "howdoyouwork": {
        "default": {
            RESPONSE: "Я функционирую благодаря комплексной платформе, которая обрабатывает голосовые команды и преобразуют их в действия.",
            PROCESSING: {"set_confidence": int_prs.set_confidence(1.0)},
        },
    },
    "howareyounew": {
        "default": {
            RESPONSE: "Я специализируюсь на управлении робототехническими комплексами и беспилотным транспортом, что делает меня уникальным среди ассистентов",
            PROCESSING: {"set_confidence": int_prs.set_confidence(1.0)},
        },
    },
    "simple": {
        "default": {
            RESPONSE: rsp.default_response,
            PROCESSING: {"set_confidence": int_prs.set_confidence(ZERO_CONFIDENCE)},
        },
    },
}

actor = Actor(flows, start_label=("service", "start"), fallback_label=("service", "fallback"))
