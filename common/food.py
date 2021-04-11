import re

OPINION_REQUESTS_ABOUT_FOOD = ["Do you like cooking?",
                               "Do you think cooking is cool?",
                               "Many people say they adore cooking. Do you agree?",
                               "Do you think cooking is a great thing?"]

OFFER_TALK_ABOUT_FOOD = ["Would you like to chat about food?",
                         "Would you like to talk about food?",
                         "I'd like to talk about food, would you?"]

TRIGGER_PHRASES = OPINION_REQUESTS_ABOUT_FOOD + OFFER_TALK_ABOUT_FOOD
FOOD_COMPILED_PATTERN = re.compile(r"\bfood", re.IGNORECASE)


def skill_trigger_phrases():
    return TRIGGER_PHRASES


def food_skill_was_proposed(prev_bot_utt):
    return any([phrase.lower() in prev_bot_utt.get('text', '').lower() for phrase in TRIGGER_PHRASES])
