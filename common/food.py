import re
from common.utils import join_sentences_in_or_pattern

OPINION_REQUESTS_ABOUT_FOOD = ["Do you like cooking?",
                               "Do you think cooking is cool?",
                               "Many people say they adore cooking. Do you agree?",
                               "Do you think cooking is a great thing?"]

OFFER_TALK_ABOUT_FOOD = ["Would you like to chat about food?",
                         "Would you like to talk about food?",
                         "I'd like to talk about food, would you?"]

FOOD_WORDS = r"(food|cook|cooking|\bbake\b|baking|cuisine|daily bread|meals|foodstuffs" \
    r"|edibles|drink|pepperoni|pizza|strawberries|chocolate|coffee|\beat\b|\bate\b" \
    r"|\beating\b|\beats\b|dinner|breakfast|\bpasta\b|burger|cheese|tasty|" \
    r"waffles|banana|\bfries\b)"

FOOD_UTTERANCES = r"(do you know .* most (favorite|favourite) food" \
    r"|.*what is your (favorite|favourite) food" \
    r"|.*by the way, what food do you like|my favou?rite food is lava cake)"
CUISINE_UTTERANCES = r"do you like .* cuisine|.*what kind of cuisine do you like"
FOOD_UTTERANCES_RE = re.compile(FOOD_UTTERANCES, re.IGNORECASE)
CUISINE_UTTERANCES_RE = re.compile(CUISINE_UTTERANCES, re.IGNORECASE)
FOOD_SKILL_TRANSFER_PHRASES = join_sentences_in_or_pattern([FOOD_UTTERANCES, CUISINE_UTTERANCES])
FOOD_SKILL_TRANSFER_PHRASES_RE = re.compile(FOOD_SKILL_TRANSFER_PHRASES, re.IGNORECASE)

WHAT_COOK = r"(what should i|what do you suggest me to)" \
    r" (cook|make for dinner)( tonight| today| tomorrow){0,1}"

TRIGGER_PHRASES = OPINION_REQUESTS_ABOUT_FOOD + OFFER_TALK_ABOUT_FOOD
FOOD_COMPILED_PATTERN = re.compile(join_sentences_in_or_pattern(
    [
        FOOD_WORDS, FOOD_SKILL_TRANSFER_PHRASES, WHAT_COOK
    ]
), re.IGNORECASE)


def skill_trigger_phrases():
    return TRIGGER_PHRASES


def food_skill_was_proposed(prev_bot_utt):
    return any([phrase.lower() in prev_bot_utt.get('text', '').lower() for phrase in TRIGGER_PHRASES])
