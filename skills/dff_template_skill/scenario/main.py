import logging
import re

from dff.core.keywords import PROCESSING, TRANSITIONS, GRAPH, RESPONSE, GLOBAL_TRANSITIONS
from dff.core import Actor
import dff.conditions as cnd
import dff.transitions as trn
import dff.response as rsp

import common.dff.integration.condition as int_cnd
import common.dff.integration.processing as int_prs
import common.dff.integration.response as int_rsp

import common.books as common_books
import common.movies as common_movies


from . import condition as loc_cnd
from . import response as loc_rsp
from . import processing as loc_prs

logger = logging.getLogger(__name__)

offered_more = cnd.any([
    cnd.negation(loc_cnd.covid_facts_exhausted),
    cnd.negation(loc_cnd.asked_about_age),
])

replied_to_offer = {
    ("covid_fact", "replied_no"): cnd.all([offered_more, int_cnd.is_no_vars]),
    ("covid_fact", "feel_fear"): cnd.all([offered_more, loc_cnd.emotion_detected("fear", 0.9)]),
    ("covid_fact", "replied_yes"): cnd.all([offered_more, int_cnd.is_yes_vars]),
    ("simple", "age_covid_risks"): cnd.all([offered_more, loc_cnd.age_detected]),
    ("covid_fact", "core_fact_2"): cnd.all([offered_more, cnd.negation(loc_cnd.age_detected)])
}

about_virus = cnd.regexp(
    r"(virus|\bcovid\b|\bill\b|infect|code nineteen|corona|corana|corono|kroner)", re.IGNORECASE
)


about_coronavirus = cnd.all([
    about_virus,
    cnd.any([
        cnd.regexp(r"(corona|corana|corono|clone a|colonel|chrono|quran|corvette|current|kroner|corolla|"
                   r"crown|volume|karuna|toronow|chrome|code nineteen|covids)", re.IGNORECASE),
        cnd.regexp(r"(outbreak|pandemy|epidemy|pandemi|epidemi)", re.IGNORECASE)
    ])
])

flows = {
    "global": {
        GRAPH: {
            "start": {
                RESPONSE: ""
            },
            "fallback": {
                RESPONSE: "",
                PROCESSING: [int_prs.set_confidence(0)]
            },
        }
    },
    "simple": {
        GLOBAL_TRANSITIONS: {
            "quarantine_end": cnd.all([
                cnd.regexp(r"quarantine", re.IGNORECASE),
                cnd.regexp(r"(\bend\b|\bover\b)", re.IGNORECASE)
            ]),
            "uninteresting_topic": cnd.regexp(
                r"(don't like|don't want to talk|don't want to hear|not concerned about|"
                r"over the coronavirus|no coronavirus|stop talking about|no more coronavirus|"
                r"don't want to listen)",
                re.IGNORECASE,
            ),
            "bot_has_covid": cnd.all([
                cnd.regexp(
                    r"(do you have|have you got|are you getting|have you ever got|are you sick with|"
                    r"have you come down with)",
                    re.IGNORECASE,
                ),
                about_virus
            ]),
            "vaccine_safety": cnd.all([
                cnd.regexp(r"(vaccine|vaccination)", re.IGNORECASE),
                cnd.regexp(r"(should i|safe)", re.IGNORECASE)
            ]),
            "user_feel_emotion": cnd.any([
                loc_cnd.emotion_detected("fear"),
                loc_cnd.emotion_detected("anger"),
            ]),
            "user_resilience_to_covid": cnd.regexp(r"(what are my chances|will i die)", re.IGNORECASE),
            "covid_symptoms": cnd.all([
                cnd.regexp(r"(symptoms|do i have|tell from|if i get)", re.IGNORECASE),
                about_coronavirus
            ]),
            "covid_treatment": cnd.regexp(r"(cure|treatment|vaccine)", re.IGNORECASE),
            "asthma_mentioned": cnd.regexp(r"(asthma)"),
            "covid_advice": cnd.all([
                cnd.regexp(r"(what if|to do| should i do)", re.IGNORECASE),
                about_coronavirus
            ]),
            "covid_origin": cnd.all([
                cnd.regexp(r"(origin|come from|where did it start)", re.IGNORECASE),
                about_coronavirus
            ]),
            "what_is_covid": cnd.regexp(r"(what is corona|what's corona|what is the pandemic)", re.IGNORECASE),
            ("subject_detected", "clarify_intention"): cnd.all([
                loc_cnd.subject_detected,
                cnd.all([about_virus, cnd.negation(about_coronavirus)])
            ]),
            ("subject_detected", "subject_stats"): cnd.all([
                loc_cnd.subject_detected,
                about_coronavirus
            ]),
            ("subject_undetected", "clarify_intention"): cnd.all([
                cnd.negation(loc_cnd.subject_detected),
                cnd.all([about_virus, cnd.negation(about_coronavirus)])
            ]),
            ("covid_fact", "core_fact_2"): cnd.regexp(
                r"(death|\bdie\b|\bdied\b|\bdying\b|mortality|how many desk)", re.IGNORECASE
            ),
            ("covid_fact", "replied_yes"): cnd.true
        },
        GRAPH: {
            "quarantine_end": {
                RESPONSE: "Although most American states are easing the restrictions, "
                          "the Coronavirus pandemics in the majority of the states hasn't been reached yet. "
                          "If you want to help ending it faster, please continue social distancing as much as you can.",
                PROCESSING: [int_prs.set_confidence(0.95)]
            },
            "uninteresting_topic": {
                RESPONSE: "",
                PROCESSING: [int_prs.set_confidence(0)]
            },
            "bot_has_covid": {
                RESPONSE: "As a socialbot, I don't have coronavirus. I hope you won't have it either.",
                PROCESSING: [int_prs.set_confidence(0.95)]
                # offer_more should be here by original idea, but it's useless due default function arguments
                # in legacy version of code (see coronavirus_skill.scenario: 554 and 375)
            },
            "vaccine_safety": {
                RESPONSE: "All CDC-approved vaccines are safe enough for you - "
                          "of course, if your doctor does not mind against using them. "
                          "I can't say the same about getting infected, however, "
                          "so vaccines are necessary to prevent people from that..",
                PROCESSING: [int_prs.set_confidence(0.95)]
            },
            "user_feel_emotion": {
                RESPONSE: rsp.choice([
                    "Please, calm down. We are a strong nation, we are vaccinating people "
                    "and we will overcome this disease one day.",
                    "Please, chin up. We have already defeated a hell lot of diseases, "
                    "and I am sure that coronavirus will be the next one."
                ]),
                PROCESSING: [int_prs.set_confidence(0.95)]
            },
            "user_resilience_to_covid": {
                RESPONSE: "As I am not your family doctor, "
                          "my knowledge about your resilience to coronavirus is limited. "
                          "Please, check the CDC website for more information.",
                PROCESSING: [int_prs.set_confidence(0.95)]
            },
            "covid_symptoms": {
                RESPONSE: "According to the CDC website, "
                          "The main warning signs of coronavirus are: "
                          "difficulty breathing or shortness of breath, "
                          "persistent pain or pressure in the chest, "
                          "new confusion or inability to arouse, "
                          "bluish lips or face. If you develop any of these signs, "
                          "get a medical attention.",
                PROCESSING: [int_prs.set_confidence(1), loc_prs.offer_more],
                TRANSITIONS: replied_to_offer
            },
            "covid_treatment": {
                RESPONSE: "There is no cure designed for COVID-19 yet. "
                          "You can consult with CDC.gov website for detailed "
                          "information about the ongoing work on the cure.",
                PROCESSING: [int_prs.set_confidence(0.9), loc_prs.offer_more],
                TRANSITIONS: replied_to_offer
            },
            "asthma_mentioned": {
                RESPONSE: "As you have asthma, I know that you should be especially "
                          "cautious about coronavirus. Unfortunately, I am not allowed to "
                          "give any recommendations about coronavirus. You can check the CDC "
                          "website for more info.",
                PROCESSING: [int_prs.set_confidence(1), loc_prs.offer_more],
                TRANSITIONS: replied_to_offer
            },
            "covid_advice": {
                RESPONSE: "Unfortunately, I am not allowed to give any recommendations "
                          "about coronavirus. You can check the CDC website for more info.",
                PROCESSING: [int_prs.set_confidence(1), loc_prs.offer_more],
                TRANSITIONS: replied_to_offer
            },
            "covid_origin": {
                RESPONSE: "According to the scientific data, coronavirus COVID 19 is a product of natural evolution. "
                          "The first place where it caused an outbreak is the city of Wuhan, China.",
                PROCESSING: [int_prs.set_confidence(0.98)]
            },
            "what_is_covid": {
                RESPONSE: "Coronavirus COVID 19 is an infectious disease. "
                          "Its common symptoms include fever, cough, shortness of breath, and many others."
                          "Anyone can have mild to severe symptoms. While the majority of cases result in mild "
                          "symptoms, some cases can be lethal. Older adults and people who have severe underlying "
                          "medical conditions like heart or lung disease or diabetes seem to be at higher risk for "
                          "developing more serious complications from COVID-19 illness.",
                PROCESSING: [int_prs.set_confidence(0.98), loc_prs.offer_more],
                TRANSITIONS: replied_to_offer
            },
            "age_covid_risks": {
                RESPONSE: loc_rsp.tell_age_risks,
                PROCESSING: [
                    int_prs.set_confidence(1),
                    loc_prs.detect_age,
                    loc_prs.execute_response,
                    loc_prs.add_from_options([
                        "While staying at home, you may use a lot of different online cinema.",
                        "While staying at home, you may read a lot of different books."
                    ])
                ]
            }
        }
    },
    "covid_fact": {
        GRAPH: {
            "replied_no": {
                RESPONSE: "Okay! I hope that this coronavirus will disappear! Now it is better to stay home.",
                # human_attr["coronavirus_skill"]["stop"] = True ???
                PROCESSING: [
                    int_prs.set_confidence(0.98),
                    loc_prs.add_from_options([
                        common_books.SWITCH_BOOK_SKILL_PHRASE,
                        common_movies.SWITCH_MOVIE_SKILL_PHRASE
                    ])
                ]
            },
            "feel_fear": {
                RESPONSE: "Just stay home, wash your hands and you will be fine. We will get over it.",
                PROCESSING: [int_prs.set_confidence(0.95)]
            },
            "replied_yes": {
                RESPONSE: loc_rsp.get_covid_fact,
                PROCESSING: [int_prs.set_confidence(1), loc_prs.execute_response, loc_prs.offer_more],
                TRANSITIONS: replied_to_offer
            },
            "core_fact_1": {
                RESPONSE: "According to the recent data, there are {0} confirmed cases of coronavirus. "
                          "Shall I tell you more?",
                PROCESSING: [
                    int_prs.set_confidence(1),
                    loc_prs.insert_global_confirmed,
                    loc_prs.set_flag("core_fact_1", True)
                ],
                TRANSITIONS: {
                    "replied_no": int_cnd.is_no_vars,
                    "feel_fear": loc_cnd.emotion_detected("fear", 0.9),
                    "replied_yes": int_cnd.is_yes_vars
                }
            },
            "core_fact_2": {
                RESPONSE: "According to the recent data, there are {0} confirmed deaths from coronavirus.",
                PROCESSING: [
                    int_prs.set_confidence(1),
                    loc_prs.insert_global_deaths,
                    loc_prs.offer_more,
                    loc_prs.set_flag("core_fact_2", True)
                ],
                TRANSITIONS: replied_to_offer
            }
        }
    },
    "subject_detected": {
        GRAPH: {
            "clarify_intention": {
                RESPONSE: "I suppose you are asking about coronavirus in {0}. Is it right?",
                PROCESSING: [
                    int_prs.set_confidence(0.99),
                    loc_prs.detect_subject,
                    loc_prs.insert_subject
                ],
                TRANSITIONS: {
                    "subject_stats": int_cnd.is_yes_vars
                }
            },
            "subject_stats": {
                RESPONSE: loc_rsp.tell_subject_stats,
                PROCESSING: [
                    int_prs.set_confidence(0.95),
                    loc_prs.detect_subject,
                    loc_prs.execute_response,
                    loc_prs.offer_more
                ],
                TRANSITIONS: replied_to_offer
            }
        }
    },
    "subject_undetected": {
        GRAPH: {
            "clarify_intention": {
                RESPONSE: "I suppose you are asking about coronavirus. Is it right?",
                PROCESSING: [int_prs.set_confidence(1)],
                TRANSITIONS: {
                    ("covid_fact", "core_fact_1"): cnd.all([
                        cnd.negation(loc_cnd.check_flag("core_fact_1")),
                        cnd.any([
                            int_cnd.is_yes_vars,
                            about_coronavirus
                        ])
                    ])
                }
            }
        }
    }
}

actor = Actor(flows, start_node_label=("global", "start"), fallback_node_label=("global", "fallback"))
