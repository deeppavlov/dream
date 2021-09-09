import logging
import re

import dff.conditions as cnd
from dff.core import Context, Actor

import common.dff.integration.condition as int_cnd
from common.utils import get_emotions
from tools.detectors import get_subject, get_age

logger = logging.getLogger(__name__)


def emotion_detected(name="fear", threshold=0.8):
    def emotion_detected_handler(ctx: Context, actor: Actor, *args, **kwargs):
        emotion_probs = get_emotions(ctx.last_request, probs=True)
        return emotion_probs.get(name, 0) >= threshold

    return emotion_detected_handler


def covid_facts_exhausted(ctx: Context, actor: Actor, *args, **kwargs):
    # In legacy version of code default value is "True", however
    # function becomes useless with it
    # (see coronavirus_skill.scenario: 375)
    return ctx.misc.get("covid_facts_exhausted", False)


def check_flag(flag: str, default: bool = False):
    def check_flag_handler(ctx: Context, actor: Actor, *args, **kwargs):
        return ctx.misc.get(flag, default)

    return check_flag_handler


def subject_detected(ctx: Context, actor: Actor, *args, **kwargs):
    # In order to increase performance
    # we need to cache value and use it
    # across all condition checks in the same 'turn'.
    # HOWEVER, there is no way to access 'context' object,
    # because it is just deepcopy, but not actual 'context'.
    # MOREOVER, we should to perform subject detection
    # again in 'processing', because we cannot just
    # save detected state into context here.
    subject = get_subject(ctx)

    if subject and subject["type"] != "undetected":
        return True

    return False


def age_detected(ctx: Context, actor: Actor, *args, **kwargs):
    # See note in subject_detected
    age = get_age(ctx)

    if age:
        return True

    return False


offered_more = cnd.any(
    [
        cnd.negation(covid_facts_exhausted),
        cnd.negation(check_flag("asked_about_age")),
    ]
)

replied_to_offer = {
    ("covid_fact", "replied_no"): cnd.all([offered_more, int_cnd.is_no_vars]),
    ("covid_fact", "feel_fear"): cnd.all([offered_more, emotion_detected("fear", 0.9)]),
    ("covid_fact", "replied_yes"): cnd.all([offered_more, int_cnd.is_yes_vars]),
    ("simple", "age_covid_risks"): cnd.all([offered_more, age_detected]),
    ("covid_fact", "core_fact_2"): cnd.all([offered_more, cnd.negation(age_detected)]),
}

about_virus = cnd.regexp(r"(virus|\bcovid\b|\bill\b|infect|code nineteen|corona|corana|corono|kroner)", re.IGNORECASE)

about_coronavirus = cnd.all(
    [
        about_virus,
        cnd.any(
            [
                cnd.regexp(
                    r"(corona|corana|corono|clone a|colonel|chrono|quran|corvette|current|kroner|corolla|"
                    r"crown|volume|karuna|toronow|chrome|code nineteen|covids)",
                    re.IGNORECASE,
                ),
                cnd.regexp(r"(outbreak|pandemy|epidemy|pandemi|epidemi)", re.IGNORECASE),
            ]
        ),
    ]
)
