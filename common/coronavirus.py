import re
from random import choice

from common.books import SWITCH_BOOK_SKILL_PHRASE
from common.movies import SWITCH_MOVIE_SKILL_PHRASE
from common.utils import is_yes, is_no


REMOTE_WORK_CORONAVIRUS_PHRASE = "Are you staying at home and working remotely to avoid coronavirus?"
STAY_HOME_CORONAVIRUS_PHRASE = "Are you staying at home to avoid coronavirus?"
CORONA_SWITCH_BEGIN = "Okay! I hope that this coronavirus will disappear! Now it is better to stay home. "


def skill_trigger_phrases():
    return [REMOTE_WORK_CORONAVIRUS_PHRASE, STAY_HOME_CORONAVIRUS_PHRASE]


VACCINE_TEMPLATE = re.compile(r'(vaccine|vaccination)', re.IGNORECASE)
SAFETY_TEMPLATE = re.compile(r'(should i|safe)', re.IGNORECASE)


def vaccine_safety_request(user_utt):
    user_utt_text = user_utt.get('text', '')
    return re.search(VACCINE_TEMPLATE, user_utt_text) and re.search(SAFETY_TEMPLATE, user_utt_text)


def corona_skill_was_proposed(prev_bot_utt):
    return REMOTE_WORK_CORONAVIRUS_PHRASE.lower() in prev_bot_utt.get('text', '').lower()


def corona_switch_skill_reply():
    reply = CORONA_SWITCH_BEGIN
    chosen = choice([SWITCH_BOOK_SKILL_PHRASE, SWITCH_MOVIE_SKILL_PHRASE])
    return reply + chosen


def is_staying_home_requested(prev_bot_utt, user_utt):
    for phrase in [REMOTE_WORK_CORONAVIRUS_PHRASE, STAY_HOME_CORONAVIRUS_PHRASE]:
        if phrase.lower() in prev_bot_utt.get('text', '').lower():
            if is_yes(user_utt) or is_no(user_utt):
                return True
    return False


death_compiled = re.compile(r"(death|\bdie\b|\bdied\b|\bdying\b|mortality|how many desk)", re.IGNORECASE)


def check_about_death(last_utterance):
    if isinstance(last_utterance, str):
        last_utterance = {'text': last_utterance}
    if re.search(death_compiled, last_utterance['text']):
        return True
    return False


quarantine_compiled = re.compile(r"quarantine", re.IGNORECASE)
end_over_compiled = re.compile(r"(\bend\b|\bover\b)", re.IGNORECASE)


def quarantine_end(last_utterance):
    if isinstance(last_utterance, str):
        last_utterance = {'text': last_utterance}
    if re.search(quarantine_compiled, last_utterance['text']) and re.search(end_over_compiled, last_utterance['text']):
        return True
    return False


virus_compiled = re.compile(r"(virus|\bcovid\b|\bill\b|infect|code nineteen|corona|corana|corono|"
                            r"kroner)", re.IGNORECASE)


def about_virus(annotated_phrase):
    if isinstance(annotated_phrase, str):
        annotated_phrase = {'text': annotated_phrase}
    if re.search(virus_compiled, annotated_phrase['text']):
        return True
    return False
