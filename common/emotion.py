import re
from common.greeting import HOW_ARE_YOU_RESPONSES
from common.utils import get_emotions
from common.universal_templates import if_chat_about_particular_topic

POSITIVE_EMOTIONS = set(['interest', 'inspiration', 'enthusiasm', 'laughter', 'amusement',
                         'empathy', 'curiosity', 'cheer', 'contentment', 'calmness', 'serenity',
                         'peace', 'trust', 'bliss', 'delight', 'happiness', 'pleasure', 'joy',
                         'carefree', 'ease', 'satisfaction', 'fulfillment', 'hopeful', 'confidence',
                         'optimism', 'passion', 'harmony', 'excitement', 'gratitude', 'kindness',
                         'affection', 'love', 'surprise', 'good', 'well', 'amazing'])

NEGATIVE_EMOTIONS = set(['grief', 'sorrow', 'heartache', 'sadness', 'unhappiness', 'depression',
                         'hatred', 'blame', 'regret', 'misery', 'resentment', 'threatening', 'antagonism',
                         'anger', 'fury', 'hostility', 'hate', 'shame', 'insecurity', 'self-consciousness',
                         'bravado', 'embarrassment', 'worry', 'panic', 'frustration', 'pessimistic',
                         'cynicism', 'jealousy', 'weariness', 'pain', 'anxiety', 'fright', 'fear', 'sad',
                         'bored', 'sick', 'bad'])
POSITIVE_EMOTION = 'positive_emotion'
NEGATIVE_EMOTION = 'negative_emotion'

HOW_DO_YOU_FEEL = 'How do you feel?'

# templates
PAIN_PATTERN = r"(\bpain\b|backache|earache|headache|stomachache|toothache|heart attack)"
SAD_PATTERN = r"\b(sad|horrible|depressed|awful|dire|upset|trash|^(\w{0,15} )?bad[?.!]?$)\b"
POOR_ASR_PATTERN = r'^say$'

PAIN_TEMPLATE = re.compile(PAIN_PATTERN, re.IGNORECASE)
LONELINESS_TEMPLATE = re.compile(r"(i am alone|lonely|loneliness|do you love me)", re.IGNORECASE)
SAD_TEMPLATE = re.compile(rf"({SAD_PATTERN}|{POOR_ASR_PATTERN})", re.IGNORECASE)
BORING_TEMPLATE = re.compile(r"(boring|bored)", re.IGNORECASE)  # The template is used to EXCLUDE answers on this intent
JOKE_REQUEST_TEMPLATE = re.compile(r"(((tell me|tell|hear)( [a-z]+){0,3} jokes?)|^joke)", re.IGNORECASE)
ADVICE_REQUEST_TEMPLATE = re.compile(r"((can|could) you )?give (me )?(a |an |some )?advice", re.IGNORECASE)
TALK_ABOUT_EMO_TEMPLATE = re.compile(r'\b(emotion|feeling|i feel\b|depress)', re.IGNORECASE)


def talk_about_emotion(user_utt, bot_uttr):
    return if_chat_about_particular_topic(user_utt, bot_uttr, compiled_pattern=TALK_ABOUT_EMO_TEMPLATE)


def is_sad(annotated_uttr):
    return re.search(SAD_TEMPLATE, annotated_uttr['text'])


def is_boring(annotated_uttr):
    return re.search(BORING_TEMPLATE, annotated_uttr['text'])


def is_pain(annotated_uttr):
    for entity in annotated_uttr.get('conceptnet', {}):
        if 'pain' in entity.get('isSymbolOf', []):
            return True
    return re.search(PAIN_TEMPLATE, annotated_uttr['text'])


def is_alone(annotated_uttr):
    return re.search(LONELINESS_TEMPLATE, annotated_uttr['text'])


def is_joke_requested(annotated_uttr):
    return bool(re.search(JOKE_REQUEST_TEMPLATE, annotated_uttr['text']))


def emo_advice_requested(uttr):
    return bool(re.search(ADVICE_REQUEST_TEMPLATE, uttr))


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
    emo_prob_threshold = 0.8  # to check if any emotion has at least this prob
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
    joke_request_detected = is_joke_requested(user_utt)
    talk_about_regexp = talk_about_emotion(user_utt, bot_uttr)
    pain_detected_by_regexp = is_pain(user_utt)
    sadness_detected_by_regexp = is_sad(user_utt)
    loneliness_detected_by_regexp = is_alone(user_utt)
    advice_request_detected_by_regexp = emo_advice_requested(user_utt.get("text", ""))
    detected_from_feel_answer = emotion_from_feel_answer(bot_uttr.get("text", ""),
                                                         user_utt.get("text", ""))
    should_run_emotion = any([emo_found_emotion,
                              joke_request_detected,
                              sadness_detected_by_regexp,
                              loneliness_detected_by_regexp,
                              pain_detected_by_regexp,
                              advice_request_detected_by_regexp,
                              talk_about_regexp,
                              detected_from_feel_answer,
                              how_are_you]) and not_strange_emotion_prob
    return should_run_emotion
