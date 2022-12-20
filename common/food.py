import re
from common.utils import join_sentences_in_or_pattern
from common.utils import get_topics, TOPIC_GROUPS

OPINION_REQUESTS_ABOUT_FOOD = [
    "Do you like cooking?",
    "Do you think cooking is cool?",
    "Many people say they adore cooking. Do you agree?",
    "Do you think cooking is a great thing?",
]

FOOD_WORDS = (
    r"(food|cook|cooking|\bbake\b|baking|cuisine|daily bread|meals|foodstuffs"
    r"|edibles|drink|pepperoni|pizza|strawberries|chocolate|coffee|\beat\b|\bate\b"
    r"|\beating\b|\beats\b|dinner|breakfast|\bpasta\b|burger|cheese|tasty|"
    r"waffles|banana|\bfries\b|\bdairy\b|\bfrench fries\b)"
)

FOOD_UTTERANCES = (
    r"(do you know .* most (favorite|favourite) food"
    r"|.*what is your (favorite|favourite) food"
    r"|.*by the way, what food do you like|my favou?rite food is lava cake)"
)
CUISINE_UTTERANCES = r"do you like .* cuisine|.*what kind of cuisine do you like"
FOOD_UTTERANCES_RE = re.compile(FOOD_UTTERANCES, re.IGNORECASE)
CUISINE_UTTERANCES_RE = re.compile(CUISINE_UTTERANCES, re.IGNORECASE)
FOOD_SKILL_TRANSFER_PHRASES = join_sentences_in_or_pattern([FOOD_UTTERANCES, CUISINE_UTTERANCES])
FOOD_SKILL_TRANSFER_PHRASES_RE = re.compile(FOOD_SKILL_TRANSFER_PHRASES, re.IGNORECASE)

WHAT_COOK = r"(what should i|what do you suggest me to)" r" (cook|make for dinner)( tonight| today| tomorrow){0,1}"

TRIGGER_PHRASES = OPINION_REQUESTS_ABOUT_FOOD
FOOD_COMPILED_PATTERN = re.compile(
    join_sentences_in_or_pattern([FOOD_WORDS, FOOD_SKILL_TRANSFER_PHRASES, WHAT_COOK]), re.IGNORECASE
)

FAST_FOOD_FACTS = [
    "roughly 50 million Americans eat at fast food restaurants in the United States each day.",
    "the first fast food was fried fish in ancient Greece.",
    "Pizza Hut was the first firm to deliver pizza to outer space. They delivered"
    " the pizza to International Space Station in 2001. This pizza was delivered "
    "by Russian rocket and Russian space agency was paid by Pizza Hut about $1,000,000 to deliver it.",
]
FAST_FOOD_QUESTIONS = [
    "Do you like to eat junk food?",
    "How often do you eat fast food?",
    "Do you like to eat at fast food restaurants?",
]
FAST_FOOD_WHAT_QUESTIONS = [
    "What do you usually eat?",
    "What type of fast food you have not tried yet?",
    "If you had to choose one fast food meal what it would be?",
]
CONCEPTNET_SYMBOLOF_FOOD = [
    "food",
    "coffee",
    "sweetness",
    "hunger",
    "breakfast",
    "dinner",
    "pizza",
    "potato",
    "meal",
    "japanese cuisine",
    "sushi",
    "italian cuisine",
    "dairy",
]
CONCEPTNET_HASPROPERTY_FOOD = ["delicious", "tasty", "sweet", "good with potato", "edible"]
CONCEPTNET_CAUSESDESIRE_FOOD = [
    "eat",
    "eat chocolate",
    "eat breakfast",
    "eat food",
    "eat quickly",
    "eat hamburger",
    "eat potato",
    "have meal",
    "have breakfast",
    "have food",
    "have steak",
    "cook dinner",
    "cook potato",
    "cook meal",
    "cook food",
    "cook pasta",
]
ACKNOWLEDGEMENTS = {
    "cuisine": "I think you're just being humble.",
    "fav_food_cook": "Okay. Just give it a chance. Hope you will enjoy it!",
}

FOOD_FACT_ACKNOWLEDGEMENTS = [
    "Your taste in food is so exquisite! I like ENTITY too. ",
    "Great choice! I'm okay with ENTITY. ",
    "Your have a good taste! ENTITY is awesome. ",
    "Wow! We are food soulmates! I enjoy eating ENTITY every time. ",
    "Mmm, ENTITY. You're a gourmet! ",
    "ENTITY. Yummy! I love it too. ",
]


def skill_trigger_phrases():
    return TRIGGER_PHRASES


def food_skill_was_proposed(prev_bot_utt):
    return any([phrase.lower() in prev_bot_utt.get("text", "").lower() for phrase in TRIGGER_PHRASES])


def about_food(annotated_utterance):
    found_topics = get_topics(annotated_utterance, probs=False, which="all")
    if any([food_topic in found_topics for food_topic in TOPIC_GROUPS["food"]]):
        return True
    elif re.findall(FOOD_COMPILED_PATTERN, annotated_utterance["text"]):
        return True
    else:
        return False
