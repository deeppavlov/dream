import re
from common.greeting import HOW_ARE_YOU_RESPONSES
from common.utils import get_emotions


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

SAD_TEMPLATE = r"(sad|horrible|depressed|awful|dire|pretty bad|pain|^bad$)"
JOKE_REQUEST_COMPILED_PATTERN = re.compile(r"(tell me .*joke{0,1}|tell a joke|tell joke)", re.IGNORECASE)
TALK_ABOUT_EMO_TEMPLATE = re.compile(r'talk about emotion', re.IGNORECASE)


def talk_about_emotion(uttr):
    return re.search(TALK_ABOUT_EMO_TEMPLATE, uttr)


def is_sad(uttr):
    return re.search(SAD_TEMPLATE, uttr)


def is_joke_requested(uttr):
    return bool(re.search(JOKE_REQUEST_COMPILED_PATTERN, uttr))


def skill_trigger_phrases():
    return [HOW_DO_YOU_FEEL] + HOW_ARE_YOU_RESPONSES


def emotion_from_feel_answer(prev_bot_uttr, user_uttr):
    if HOW_DO_YOU_FEEL.lower() in prev_bot_uttr.lower():
        for w in user_uttr.split(" "):
            w = re.sub(r"\W", " ", w.lower()).strip()
            if w in POSITIVE_EMOTIONS:
                return POSITIVE_EMOTION
            elif w in NEGATIVE_EMOTIONS:
                return NEGATIVE_EMOTION
    return None


def if_turn_on_emotion(user_utt, bot_uttr):
    emotions = get_emotions(user_utt, probs=True)
    emo_prob_threshold = 0.9  # to check if any emotion has at least this prob
    found_emotion, found_prob = 'neutral', 1
    for emotion, prob in emotions.items():
        if prob == max(emotions.values()):
            found_emotion, found_prob = emotion, prob
    emo_found_emotion = found_emotion != 'neutral' and found_prob > emo_prob_threshold
    good_emotion_prob = max([emotions.get('joy', 0), emotions.get('love', 0)])
    bad_emotion_prob = max([emotions.get('anger', 0), emotions.get('fear', 0), emotions.get('sadness', 0)])
    not_strange_emotion_prob = not (good_emotion_prob > 0.6 and bad_emotion_prob > 0.5)
    how_are_you = any([how_are_you_response.lower() in bot_uttr.get("text", "").lower()
                       for how_are_you_response in HOW_ARE_YOU_RESPONSES])
    joke_request_detected = is_joke_requested(user_utt.get("text", ""))
    talk_about_regexp = talk_about_emotion(user_utt.get("text", ""))
    sadness_detected_by_regexp = is_sad(user_utt.get("text", ""))
    detected_from_feel_answer = emotion_from_feel_answer(bot_uttr.get("text", ""),
                                                         user_utt.get("text", ""))
    should_run_emotion = any([emo_found_emotion,
                              joke_request_detected,
                              sadness_detected_by_regexp,
                              talk_about_regexp,
                              detected_from_feel_answer,
                              how_are_you]) and not_strange_emotion_prob
    return should_run_emotion
