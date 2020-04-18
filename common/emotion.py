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


def skill_trigger_phrases():
    return [HOW_DO_YOU_FEEL]


def detect_emotion(prev_bot_utt, user_utt):
    if HOW_DO_YOU_FEEL.lower() in prev_bot_utt.get('text', '').lower():
        for w in user_utt['text'].split(" "):
            w = re.sub(r"\W", " ", w.lower()).strip()
            if w in POSITIVE_EMOTIONS:
                return POSITIVE_EMOTION
            elif w in NEGATIVE_EMOTIONS:
                return NEGATIVE_EMOTION
    return None
