import logging
import re

from df_engine.core.keywords import PROCESSING, TRANSITIONS, RESPONSE, GLOBAL
from df_engine.core import Actor
import df_engine.conditions as cnd
import df_engine.responses as rsp

import common.books as common_books
import common.dff.integration.condition as int_cnd
import common.dff.integration.processing as int_prs
import common.movies as common_movies
import scenario.condition as loc_cnd
import scenario.processing as loc_prs
import scenario.response as loc_rsp

# !WARNING!WARNING!WARNING!
# Flow for skill_trigger_phrases
# is NOT implemented in this dff version of skill.
# This decision was made because these phrases are NEVER used.
# Are they deprecated?
# Related lines:
# - coronavirus_skill:14 (skill_trigger_phrases)
# - coronavirus_skill:547 - 549 (transition condition: bot said phrase + user asked why)
# - coronavirus_skill:110 (reply to user question "why")

SUPER_CONFIDENCE = 1.0
HIGH_CONFIDENCE = 0.98
DEFAULT_CONFIDENCE = 0.95
BIT_LOWER_CONFIDENCE = 0.90
ZERO_CONFIDENCE = 0.0

# Intention to know something about covid but not in specific subject
CLARIFY_INTENTION_ABOUT_COVID_CONFIDENCE = 1
# Intention to know covid incidence statistics in specific city/county/state/country
CLARIFY_INTENTION_ABOUT_SUBJECT_CONFIDENCE = 0.99
# Detected "fear" or "anger" emotion
USER_FEEL_EMOTION_CONFIDENCE = 0.95
# Detected "fear" emotion
USER_FEEL_FEAR_CONFIDENCE = 0.90


logger = logging.getLogger(__name__)

flows = {
    "service": {
        "start": {RESPONSE: ""},
        "fallback": {RESPONSE: "", PROCESSING: {"set_confidence": int_prs.set_confidence(ZERO_CONFIDENCE)}},
    },
    GLOBAL: {
        TRANSITIONS: {
            ("simple", "quarantine_end"): cnd.all(
                [cnd.regexp(r"quarantine", re.IGNORECASE), cnd.regexp(r"(\bend\b|\bover\b)", re.IGNORECASE)]
            ),
            ("simple", "uninteresting_topic"): cnd.regexp(
                r"(don't like|don't want to talk|don't want to hear|not concerned about|"
                r"over the coronavirus|no coronavirus|stop talking about|no more coronavirus|"
                r"don't want to listen)",
                re.IGNORECASE,
            ),
            ("simple", "bot_has_covid"): cnd.all(
                [
                    cnd.regexp(
                        r"(do you have|have you got|are you getting|have you ever got|are you sick with|"
                        r"have you come down with)",
                        re.IGNORECASE,
                    ),
                    loc_cnd.about_virus,
                ]
            ),
            ("simple", "vaccine_safety"): cnd.all(
                [cnd.regexp(r"(vaccine|vaccination)", re.IGNORECASE), cnd.regexp(r"(should i|safe)", re.IGNORECASE)]
            ),
            ("simple", "user_feel_emotion"): cnd.any(
                [
                    loc_cnd.emotion_detected("fear"),
                    loc_cnd.emotion_detected("anger"),
                ]
            ),
            ("simple", "user_resilience_to_covid"): cnd.regexp(r"(what are my chances|will i die)", re.IGNORECASE),
            ("simple", "covid_symptoms"): cnd.all(
                [cnd.regexp(r"(symptoms|do i have|tell from|if i get)", re.IGNORECASE), loc_cnd.about_coronavirus]
            ),
            ("simple", "covid_treatment"): cnd.regexp(r"(cure|treatment|vaccine)", re.IGNORECASE),
            ("simple", "asthma_mentioned"): cnd.regexp(r"(asthma)"),
            ("simple", "covid_advice"): cnd.all(
                [cnd.regexp(r"(what if|to do| should i do)", re.IGNORECASE), loc_cnd.about_coronavirus]
            ),
            ("simple", "covid_origin"): cnd.all(
                [cnd.regexp(r"(origin|come from|where did it start)", re.IGNORECASE), loc_cnd.about_coronavirus]
            ),
            ("simple", "what_is_covid"): cnd.regexp(
                r"(what is corona|what's corona|what is the pandemic)", re.IGNORECASE
            ),
            ("subject_detected", "clarify_intention"): cnd.all(
                [loc_cnd.subject_detected, cnd.all([loc_cnd.about_virus, cnd.negation(loc_cnd.about_coronavirus)])]
            ),
            ("subject_detected", "subject_stats"): cnd.all([loc_cnd.subject_detected, loc_cnd.about_coronavirus]),
            ("subject_undetected", "clarify_intention"): cnd.all(
                [
                    cnd.negation(loc_cnd.subject_detected),
                    cnd.all([loc_cnd.about_virus, cnd.negation(loc_cnd.about_coronavirus)]),
                ]
            ),
            ("covid_fact", "core_fact_2"): cnd.regexp(
                r"(death|\bdie\b|\bdied\b|\bdying\b|mortality|how many desk)", re.IGNORECASE
            ),
            ("covid_fact", "replied_yes"): cnd.true(),
        },
        PROCESSING: {"set_confidence": int_prs.set_confidence(DEFAULT_CONFIDENCE)},
    },
    "simple": {
        "quarantine_end": {
            RESPONSE: "Although most American states are easing the restrictions, "
            "the Coronavirus pandemics in the majority of the states hasn't been reached yet. "
            "If you want to help ending it faster, please continue social distancing as much as you can.",
        },
        "uninteresting_topic": {RESPONSE: "", PROCESSING: {"set_confidence": int_prs.set_confidence(ZERO_CONFIDENCE)}},
        "bot_has_covid": {
            RESPONSE: "As a socialbot, I don't have coronavirus. I hope you won't have it either.",
            # offer_more should be here by original idea, but it's useless due default function arguments
            # in legacy version of code (see coronavirus_skill.scenario: 554 and 375)
        },
        "vaccine_safety": {
            RESPONSE: "All CDC-approved vaccines are safe enough for you - "
            "of course, if your doctor does not mind against using them. "
            "I can't say the same about getting infected, however, "
            "so vaccines are necessary to prevent people from that..",
        },
        "user_feel_emotion": {
            RESPONSE: rsp.choice(
                [
                    "Please, calm down. We are a strong nation, we are vaccinating people "
                    "and we will overcome this disease one day.",
                    "Please, chin up. We have already defeated a hell lot of diseases, "
                    "and I am sure that coronavirus will be the next one.",
                ]
            ),
            PROCESSING: {"set_confidence": int_prs.set_confidence(USER_FEEL_EMOTION_CONFIDENCE)},
        },
        "user_resilience_to_covid": {
            RESPONSE: "As I am not your family doctor, "
            "my knowledge about your resilience to coronavirus is limited. "
            "Please, check the CDC website for more information.",
        },
        "covid_symptoms": {
            RESPONSE: "According to the CDC website, "
            "The main warning signs of coronavirus are: "
            "difficulty breathing or shortness of breath, "
            "persistent pain or pressure in the chest, "
            "new confusion or inability to arouse, "
            "bluish lips or face. If you develop any of these signs, "
            "get a medical attention.",
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(SUPER_CONFIDENCE),
                "offer_more": loc_prs.offer_more,
            },
            TRANSITIONS: loc_cnd.replied_to_offer,
        },
        "covid_treatment": {
            RESPONSE: "There is no cure designed for COVID-19 yet. "
            "You can consult with CDC.gov website for detailed "
            "information about the ongoing work on the cure.",
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(BIT_LOWER_CONFIDENCE),
                "offer_more": loc_prs.offer_more,
            },
            TRANSITIONS: loc_cnd.replied_to_offer,
        },
        "asthma_mentioned": {
            RESPONSE: "As you have asthma, I know that you should be especially "
            "cautious about coronavirus. Unfortunately, I am not allowed to "
            "give any recommendations about coronavirus. You can check the CDC "
            "website for more info.",
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(SUPER_CONFIDENCE),
                "offer_more": loc_prs.offer_more,
            },
            TRANSITIONS: loc_cnd.replied_to_offer,
        },
        "covid_advice": {
            RESPONSE: "Unfortunately, I am not allowed to give any recommendations "
            "about coronavirus. You can check the CDC website for more info.",
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(SUPER_CONFIDENCE),
                "offer_more": loc_prs.offer_more,
            },
            TRANSITIONS: loc_cnd.replied_to_offer,
        },
        "covid_origin": {
            RESPONSE: "According to the scientific data, coronavirus COVID 19 is a product of natural evolution. "
            "The first place where it caused an outbreak is the city of Wuhan, China.",
            PROCESSING: {"set_confidence": int_prs.set_confidence(HIGH_CONFIDENCE)},
        },
        "what_is_covid": {
            RESPONSE: "Coronavirus COVID 19 is an infectious disease. "
            "Its common symptoms include fever, cough, shortness of breath, and many others."
            "Anyone can have mild to severe symptoms. While the majority of cases result in mild "
            "symptoms, some cases can be lethal. Older adults and people who have severe underlying "
            "medical conditions like heart or lung disease or diabetes seem to be at higher risk for "
            "developing more serious complications from COVID-19 illness.",
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(HIGH_CONFIDENCE),
                "offer_more": loc_prs.offer_more,
            },
            TRANSITIONS: loc_cnd.replied_to_offer,
        },
        "age_covid_risks": {
            # !WARNING!
            # See function implementation
            # for more details about linking issue
            RESPONSE: loc_rsp.tell_age_risks,
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(SUPER_CONFIDENCE),
                "detect_age": loc_prs.detect_age,
                "execute_response": loc_prs.execute_response,
                "set_flag": loc_prs.set_flag("asked_about_age", True),
            },
        },
    },
    "covid_fact": {
        "replied_no": {
            RESPONSE: "Okay! I hope that this coronavirus will disappear! Now it is better to stay home.",
            # !WARNING!
            # This line presented in original scenario:
            # 'human_attr["coronavirus_skill"]["stop"] = True'.
            # Is it still required?
            # See coronavirus_skill.scenario: 578 for more details.
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(HIGH_CONFIDENCE),
                "add_from_options": loc_prs.add_from_options(
                    [common_books.SWITCH_BOOK_SKILL_PHRASE, common_movies.SWITCH_MOVIE_SKILL_PHRASE]
                ),
            },
        },
        "feel_fear": {
            RESPONSE: "Just stay home, wash your hands and you will be fine. We will get over it.",
            PROCESSING: {"set_confidence": int_prs.set_confidence(USER_FEEL_FEAR_CONFIDENCE)},
        },
        "replied_yes": {
            RESPONSE: loc_rsp.get_covid_fact,
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(SUPER_CONFIDENCE),
                "execute_response": loc_prs.execute_response,
                "offer_more": loc_prs.offer_more,
            },
            TRANSITIONS: loc_cnd.replied_to_offer,
        },
        "core_fact_1": {
            RESPONSE: "According to the recent data, there are {0} confirmed cases of coronavirus. "
            "Shall I tell you more?",
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(SUPER_CONFIDENCE),
                "insert_global_confirmed": loc_prs.insert_global_confirmed,
                "set_flag": loc_prs.set_flag("core_fact_1", True),
            },
            TRANSITIONS: {
                "replied_no": int_cnd.is_no_vars,
                "feel_fear": loc_cnd.emotion_detected("fear", 0.9),
                "replied_yes": int_cnd.is_yes_vars,
            },
        },
        "core_fact_2": {
            RESPONSE: "According to the recent data, there are {0} confirmed deaths from coronavirus.",
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(SUPER_CONFIDENCE),
                "insert_global_deaths": loc_prs.insert_global_deaths,
                "offer_more": loc_prs.offer_more,
                "set_flag": loc_prs.set_flag("core_fact_2", True),
            },
            TRANSITIONS: loc_cnd.replied_to_offer,
        },
    },
    "subject_detected": {
        "clarify_intention": {
            RESPONSE: "I suppose you are asking about coronavirus in {0}. Is it right?",
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(CLARIFY_INTENTION_ABOUT_SUBJECT_CONFIDENCE),
                "detect_subject": loc_prs.detect_subject,
                "insert_subject": loc_prs.insert_subject,
            },
            TRANSITIONS: {"subject_stats": int_cnd.is_yes_vars},
        },
        "subject_stats": {
            RESPONSE: loc_rsp.tell_subject_stats,
            PROCESSING: {
                "detect_subject": loc_prs.detect_subject,
                "execute_response": loc_prs.execute_response,
                "offer_more": loc_prs.offer_more,
            },
            TRANSITIONS: loc_cnd.replied_to_offer,
        },
    },
    "subject_undetected": {
        "clarify_intention": {
            RESPONSE: "I suppose you are asking about coronavirus. Is it right?",
            PROCESSING: {"set_confidence": int_prs.set_confidence(CLARIFY_INTENTION_ABOUT_COVID_CONFIDENCE)},
            TRANSITIONS: {
                ("covid_fact", "core_fact_1"): cnd.all(
                    [
                        cnd.negation(loc_cnd.check_flag("core_fact_1")),
                        cnd.any([int_cnd.is_yes_vars, loc_cnd.about_coronavirus]),
                    ]
                )
            },
        }
    },
}

actor = Actor(flows, start_label=("service", "start"), fallback_label=("service", "fallback"))
