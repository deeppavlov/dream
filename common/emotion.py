import re

from common.greeting import HOW_ARE_YOU_RESPONSES
from common.utils import get_emotions, get_comet_conceptnet_annotations
from common.universal_templates import if_chat_about_particular_topic


POSITIVE_EMOTIONS = set(
    [
        "interest",
        "inspiration",
        "enthusiasm",
        "laughter",
        "amusement",
        "empathy",
        "curiosity",
        "cheer",
        "contentment",
        "calmness",
        "serenity",
        "peace",
        "trust",
        "bliss",
        "delight",
        "happiness",
        "pleasure",
        "joy",
        "carefree",
        "ease",
        "satisfaction",
        "fulfillment",
        "hopeful",
        "confidence",
        "optimism",
        "passion",
        "harmony",
        "excitement",
        "gratitude",
        "kindness",
        "affection",
        "love",
        "surprise",
        "good",
        "well",
        "amazing",
    ]
)

NEGATIVE_EMOTIONS = set(
    [
        "grief",
        "sorrow",
        "heartache",
        "sadness",
        "unhappiness",
        "depression",
        "hatred",
        "blame",
        "regret",
        "misery",
        "resentment",
        "threatening",
        "antagonism",
        "anger",
        "fury",
        "hostility",
        "hate",
        "shame",
        "insecurity",
        "self-consciousness",
        "bravado",
        "embarrassment",
        "worry",
        "panic",
        "frustration",
        "pessimistic",
        "cynicism",
        "jealousy",
        "weariness",
        "pain",
        "anxiety",
        "fright",
        "fear",
        "sad",
        "bored",
        "sick",
        "bad",
    ]
)
POSITIVE_EMOTION = "positive_emotion"
NEGATIVE_EMOTION = "negative_emotion"

HOW_DO_YOU_FEEL = "How do you feel?"

# templates
PAIN_PATTERN = (
    r"\b(pain|backache|heart attack|earache|headache|" r"stomachache|toothache|diseased|ailing|damaged|sick|sore)\b"
)
SAD_PATTERN = (
    r"\b(sad|horrible|depressed|terrible|tired|awful|dire|upset|trash|"
    r"pity|poor|ill|low|exhausted|inferior|crying|miserable|cry|naughty|nasty|foul|ugly|grisly|harmful|"
    r"spoiled|depraved|tained|awry|so so|badly|sadly|wretched|bad|unhappy)\b"
)
POSITIVE_PATTERN = (
    r"\b(happy|good|okay|great|yeah|cool|awesome|perfect|nice|well|ok|fine|"
    r"neat|swell|fabulous|peachy|excellent|exciting|excited|splendid|all right"
    r"|super|classy|tops|famous|superb|incredible|tremendous|class|crackajack|crackerjack)\b"
)
ALONE_PATTERN = r"(i am alone|lonely|loneliness|do you love me)"
NOT_PATTERN = r"((\bnot|n't\bno)( too| that| really| so| feel| going)?)"
JOKE_PATTERN = r"(((tell me|tell|hear)( [a-z]+){0,3} jokes?)|^joke)"
POOR_ASR_PATTERN = r"^say$"

POSITIVE_TEMPLATE = re.compile(POSITIVE_PATTERN, re.IGNORECASE)
NOT_POSITIVE_TEMPLATE = re.compile(rf"{NOT_PATTERN} {POSITIVE_PATTERN}", re.IGNORECASE)
PAIN_TEMPLATE = re.compile(PAIN_PATTERN, re.IGNORECASE)
NOT_PAIN_TEMPLATE = re.compile(rf"{NOT_PATTERN} {PAIN_PATTERN}", re.IGNORECASE)
LONELINESS_TEMPLATE = re.compile(rf"{ALONE_PATTERN}", re.IGNORECASE)
NOT_LONELINESS_TEMPLATE = re.compile(rf"{NOT_PATTERN} {ALONE_PATTERN}", re.IGNORECASE)
SAD_TEMPLATE = re.compile(rf"({SAD_PATTERN}|{POOR_ASR_PATTERN})", re.IGNORECASE)
NOT_SAD_TEMPLATE = re.compile(rf"{NOT_PATTERN} {SAD_PATTERN}", re.IGNORECASE)
BORING_TEMPLATE = re.compile(r"(boring|bored)", re.IGNORECASE)
NOT_BORING_TEMPLATE = re.compile(rf"{NOT_PATTERN} (boring|bored)", re.IGNORECASE)
JOKE_REQUEST_TEMPLATE = re.compile(rf"{JOKE_PATTERN}", re.IGNORECASE)
NOT_JOKE_REQUEST_TEMPLATE = re.compile(rf"{NOT_PATTERN} {JOKE_PATTERN}", re.IGNORECASE)
ADVICE_PATTERN = (
    r"((((can|could) you )?(give|suggest|tell) (me )?(a |an |some )?advice)|" r"(advice me (something|anything)))"
)
ADVICE_REQUEST_TEMPLATE = re.compile(ADVICE_PATTERN, re.IGNORECASE)

TALK_ABOUT_EMO_TEMPLATE = re.compile(r"\b(emotion|feeling|i feel\b|depress)", re.IGNORECASE)


def talk_about_emotion(user_utt, bot_uttr):
    return if_chat_about_particular_topic(user_utt, bot_uttr, compiled_pattern=TALK_ABOUT_EMO_TEMPLATE)


def is_sad(annotated_uttr):
    uttr_text = annotated_uttr["text"]
    is_sad = re.search(SAD_TEMPLATE, uttr_text) and not re.search(NOT_SAD_TEMPLATE, uttr_text)
    not_positive = re.search(NOT_POSITIVE_TEMPLATE, uttr_text)
    return is_sad or not_positive


def is_boring(annotated_uttr):
    uttr_text = annotated_uttr["text"]
    return re.search(BORING_TEMPLATE, uttr_text) and not re.search(NOT_BORING_TEMPLATE, uttr_text)


def is_pain(annotated_uttr):
    uttr_text = annotated_uttr["text"]

    for elem, triplets in get_comet_conceptnet_annotations(annotated_uttr).items():
        if "SymbolOf" in triplets and "pain" in triplets["SymbolOf"]:
            return True
    return re.search(PAIN_TEMPLATE, uttr_text) and not re.search(NOT_PAIN_TEMPLATE, uttr_text)


def is_alone(annotated_uttr):
    uttr_text = annotated_uttr["text"]
    return re.search(LONELINESS_TEMPLATE, uttr_text) and not re.search(NOT_LONELINESS_TEMPLATE, uttr_text)


def is_joke_requested(annotated_uttr):
    uttr_text = annotated_uttr["text"]
    return re.search(JOKE_REQUEST_TEMPLATE, uttr_text) and not re.search(NOT_JOKE_REQUEST_TEMPLATE, uttr_text)


def is_negative_regexp_based(annotated_uttr):
    return any([negative_function(annotated_uttr) for negative_function in [is_sad, is_boring, is_alone, is_pain]])


def is_positive_regexp_based(annotated_uttr):
    uttr_text = annotated_uttr["text"]
    positive = re.search(POSITIVE_TEMPLATE, uttr_text) and not re.search(NOT_POSITIVE_TEMPLATE, uttr_text)
    not_sad = re.search(NOT_SAD_TEMPLATE, uttr_text)
    return positive or not_sad


def emo_advice_requested(uttr):
    return bool(re.search(ADVICE_REQUEST_TEMPLATE, uttr))


def skill_trigger_phrases():
    return [HOW_DO_YOU_FEEL] + sum([HOW_ARE_YOU_RESPONSES[lang] for lang in ["RU", "EN"]], [])


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
    found_emotion, found_prob = "neutral", 1
    for emotion, prob in emotions.items():
        if prob == max(emotions.values()):
            found_emotion, found_prob = emotion, prob
    emo_found_emotion = found_emotion != "neutral" and found_prob > emo_prob_threshold
    good_emotion_prob = max([emotions.get("joy", 0), emotions.get("love", 0)])
    bad_emotion_prob = max([emotions.get("anger", 0), emotions.get("fear", 0), emotions.get("sadness", 0)])
    not_strange_emotion_prob = not (good_emotion_prob > 0.6 and bad_emotion_prob > 0.5)
    how_are_you = any(
        [
            how_are_you_response.lower() in bot_uttr.get("text", "").lower()
            for how_are_you_response in sum([HOW_ARE_YOU_RESPONSES[lang] for lang in ["RU", "EN"]], [])
        ]
    )
    joke_request_detected = is_joke_requested(user_utt)
    talk_about_regexp = talk_about_emotion(user_utt, bot_uttr)
    pain_detected_by_regexp = is_pain(user_utt)
    sadness_detected_by_regexp = is_sad(user_utt)
    loneliness_detected_by_regexp = is_alone(user_utt)
    advice_request_detected_by_regexp = emo_advice_requested(user_utt.get("text", ""))
    detected_from_feel_answer = emotion_from_feel_answer(bot_uttr.get("text", ""), user_utt.get("text", ""))
    should_run_emotion = (
        any(
            [
                emo_found_emotion,
                joke_request_detected,
                sadness_detected_by_regexp,
                loneliness_detected_by_regexp,
                pain_detected_by_regexp,
                advice_request_detected_by_regexp,
                talk_about_regexp,
                detected_from_feel_answer,
                how_are_you,
            ]
        )
        and not_strange_emotion_prob
    )
    return should_run_emotion
