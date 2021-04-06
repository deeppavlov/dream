import re
from common.utils import get_intents
from common.universal_templates import if_lets_chat_about_topic, COMPILE_WHAT_TO_TALK_ABOUT


def skill_trigger_phrases():
    return ['What is your favourite celebrity?']


def talk_about_celebrity(human_utterance, bot_utterance):
    user_lets_chat_about = (
        "lets_chat_about" in get_intents(human_utterance, which="intent_catcher")
        or if_lets_chat_about_topic(human_utterance["text"])
        or re.search(COMPILE_WHAT_TO_TALK_ABOUT, bot_utterance["text"]))
    flag = user_lets_chat_about and any([j in human_utterance['text'].lower()
                                         for j in ['celebrit', 'actor']])
    return flag
