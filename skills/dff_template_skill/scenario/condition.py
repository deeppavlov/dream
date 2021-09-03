import logging

from dff.core import Context, Actor

from common.dff.integration import condition as int_cnd
from common.utils import is_yes, is_no, get_emotions

logger = logging.getLogger(__name__)


def emotion_detected(name="fear", threshold=0.8):
    def emotion_detected_handler(ctx: Context, actor: Actor, *args, **kwargs):
        emotion_probs = get_emotions(ctx.last_request, probs=True)
        return emotion_probs.get(name, 0) > threshold

    return emotion_detected_handler


def covid_facts_exhausted(ctx: Context, actor: Actor, *args, **kwargs):
    # in legacy version of code default value is "True", however
    # function becomes useless with it
    # (see coronavirus_skill.scenario: 375)
    return ctx.misc.get("covid_facts_exhausted", False)


def asked_about_age(ctx: Context, actor: Actor, *args, **kwargs):
    # in legacy version of code default value is "True", however
    # function becomes useless with it
    # (see coronavirus_skill.scenario: 375)
    return ctx.misc.get("asked_about_age", False)
