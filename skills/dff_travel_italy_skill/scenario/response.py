import logging
from typing import Callable, List
import datetime

from df_engine.core import Context, Actor
import df_engine.conditions as cnd


from common.travel_italy import QUESTIONS_ABOUT_ITALY


logger = logging.getLogger(__name__)
# ....

START_PHRASE = "Italy is my paradise. Do you love this country?"
UNCERTAINTY = [
    " It's not always easy to tell, of course.",
    " It's only my opinion, though.",
]
FAVOURITE_PLACE_PHRASES = [
    "Do you want to know what my favourite place in Italy is?",
    "Do you want to know what my other favourite place in Italy is?",
    "Do you want to hear about one more place in Italy that impressed me?",
]
OPINION_REQUEST_ON_ITALY_PHRASES = [
    "Did you enjoy going to Italy?",
    "Did you find this place interesting?",
    "Was the trip to Italy exciting for you?",
]

VISIT_PLACE_ADVICES = [
    "You should go there one day. You won't regret it!",
    "You should put it on your bucket list!",
    "I think you would love this place!",
]

DID_NOT_EXIST = [
    "I didn't exist at that time.",
    "I'm a bit too young to remember those times though.",
]

WHAT_DID_DAY = "What did you do during the day?"

HAVE_YOU_BEEN_PLACE = "Have you been there?"
ASK_ABOUT_OFFERED_LOC = "It's a real wonder. Have you been there?"
TELL_REQUEST = "May I tell you something about this place?"
TELL_REQUEST2 = "Would you like to hear something else about this place?"
WHAT_PLACE_IMPRESSED_MOST = "What place impressed you the most?"
WHAT_PLACE_LAST_VISITED = "What place in Italy did you last visit?"
OFFER_FACT_ABOUT_PLACE = "Would you like to hear a fact about it?"
ITALY_TRAVEL_SKILL_QUESTIONS = [WHAT_PLACE_LAST_VISITED, WHAT_PLACE_IMPRESSED_MOST]
ALL_QUESTIONS_ABOUT_ITALY = QUESTIONS_ABOUT_ITALY + ITALY_TRAVEL_SKILL_QUESTIONS
WHO_TRAVEL_WITH = "Who did you go there with?"
WHEN_TRAVEL = "When did you go there?"

CURRENT_YEAR = datetime.datetime.today().year


def append_unused(initial: str, phrases: List[str], exit_on_exhaust: bool = False) -> Callable:
    """
    Return an unused or a least used response from a list of options
    """

    def unused_handler(ctx: Context, actor: Actor) -> str:
        used = ctx.misc.get("used_phrases", [])
        confidences = [1] * len(phrases)

        for idx, phrase in enumerate(phrases):
            times: int = used.count(id(phrase))
            if times == 0:
                used.append(id(phrase))
                ctx.misc["used_phrases"] = used
                return initial + phrase
            confidences[idx] *= 0.4**times

        if exit_on_exhaust:
            label = ctx.last_label
            actor.plot[label[0]][label[1]].transitions = {("global_flow", "fallback", 2): cnd.true()}
            return initial

        target_idx = confidences.index(max(confidences))
        target_phrase = phrases[target_idx]
        used.append(id(target_phrase))
        ctx.misc["used_phrases"] = used
        return initial + target_phrase

    return unused_handler
