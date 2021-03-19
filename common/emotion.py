import re


POSITIVE_EMOTIONS = set(['interest', 'inspiration', 'enthusiasm', 'laughter', 'amusement',
                         'empathy', 'curiosity', 'cheer', 'contentment', 'calmness', 'serenity',
                         'peace', 'trust', 'bliss', 'delight', 'happiness', 'pleasure', 'joy',
                         'carefree', 'ease', 'satisfaction', 'fulfillment', 'hopeful', 'confidence',
                         'optimism', 'passion', 'harmony', 'excitement', 'gratitude', 'kindness',
                         'affection', 'love', 'surprise'])

NEGATIVE_EMOTIONS = set(['grief', 'sorrow', 'heartache', 'sadness', 'unhappiness', 'depression',
                         'hatred', 'blame', 'regret', 'misery', 'resentment', 'threatening', 'antagonism',
                         'anger', 'fury', 'hostility', 'hate', 'shame', 'insecurity', 'self-consciousness',
                         'bravado', 'embarrassment', 'worry', 'panic', 'frustration', 'pessimistic',
                         'cynicism', 'jealousy', 'weariness', 'pain', 'anxiety', 'fright', 'fear', 'sad',
                         'bored', 'sick', 'bad'])
POSITIVE_EMOTION = 'positive_emotion'
NEGATIVE_EMOTION = 'negative_emotion'

HOW_DO_YOU_FEEL = 'How do you feel?'

SAD_TEMPLATE = r"^(sad|horrible|depressed|awful|dire|died)\.?$"


def is_sad(uttr):
    return re.search(SAD_TEMPLATE, uttr)


def is_joke_requested(uttr):
    return bool(re.match("tell me .*joke(s){0,1}", uttr))


def skill_trigger_phrases():
    return [HOW_DO_YOU_FEEL]


def emotion_from_feel_answer(prev_bot_uttr, user_uttr):
    if HOW_DO_YOU_FEEL.lower() in prev_bot_uttr.lower():
        for w in user_uttr.split(" "):
            w = re.sub(r"\W", " ", w.lower()).strip()
            if w in POSITIVE_EMOTIONS:
                return POSITIVE_EMOTION
            elif w in NEGATIVE_EMOTIONS:
                return NEGATIVE_EMOTION
    return None
