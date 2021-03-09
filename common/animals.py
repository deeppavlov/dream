import re

LIKE_ANIMALS_REQUESTS = ["Do you like animals?"]
HAVE_PETS_REQUESTS = ["Do you have pets?"]

OFFER_TALK_ABOUT_ANIMALS = ["Would you like to talk about animals?",
                            "Let's chat about animals. Do you agree?",
                            "I'd like to talk about animals, would you?"
                            ]

TRIGGER_PHRASES = LIKE_ANIMALS_REQUESTS + HAVE_PETS_REQUESTS + OFFER_TALK_ABOUT_ANIMALS


def skill_trigger_phrases():
    return TRIGGER_PHRASES


def animals_skill_was_proposed(prev_bot_utt):
    return any([phrase.lower() in prev_bot_utt.get('text', '').lower() for phrase in TRIGGER_PHRASES])


PETS_TEMPLATE = re.compile(r"(cat|dog|horse|puppy|kitty|kitten|parrot|rat|mouse|hamster)", re.IGNORECASE)
COLORS_TEMPLATE = re.compile(r"(black|white|yellow|blue|green|brown|orange|spotted|striped)", re.IGNORECASE)
