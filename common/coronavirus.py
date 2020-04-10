from random import choice
from common.books import SWITCH_BOOK_SKILL_PHRASE
from common.movies import SWITCH_MOVIE_SKILL_PHRASE
from common.utils import is_yes, is_no


REMOTE_WORK_CORONAVIRUS_PHRASE = "Are you staying at home and working remotely to avoid coronavirus?"
STAY_HOME_CORONAVIRUS_PHRASE = "Are you staying at home to avoid coronavirus?"


def skill_trigger_phrases():
    return [REMOTE_WORK_CORONAVIRUS_PHRASE, STAY_HOME_CORONAVIRUS_PHRASE]


def corona_skill_was_proposed(prev_bot_utt):
    return REMOTE_WORK_CORONAVIRUS_PHRASE.lower() in prev_bot_utt.get('text', '').lower()


def corona_switch_skill_reply():
    reply = "Okay! I believe that this coronavirus will disappear! Now it is better to stay home. "
    chosen = choice([SWITCH_BOOK_SKILL_PHRASE, SWITCH_MOVIE_SKILL_PHRASE])
    return reply + chosen


def is_staying_home_requested(prev_bot_utt, user_utt):
    for phrase in [REMOTE_WORK_CORONAVIRUS_PHRASE, STAY_HOME_CORONAVIRUS_PHRASE]:
        if phrase.lower() in prev_bot_utt.get('text', '').lower():
            if is_yes(user_utt) or is_no(user_utt):
                return True
    return False
