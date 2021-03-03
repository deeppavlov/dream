import re

LIKE_ANIMALS_REQUESTS = ["Do you like animals?"]
HAVE_PETS_REQUESTS = ["Do you have pets?"]

OFFER_TALK_ABOUT_ANIMALS = ["Would you like to talk about animals?",
                            "Let's chat about animals. Do you agree?",
                            "I'd like to talk about animals, would you?"
                            ]


def skill_trigger_phrases():
    return LIKE_ANIMALS_REQUESTS + HAVE_PETS_REQUESTS + OFFER_TALK_ABOUT_ANIMALS


PETS_TEMPLATE = re.compile(r"(cat|dog|horse|puppy|kitty|kitten|parrot|rat|mouse|hamster)", re.IGNORECASE)
COLORS_TEMPLATE = re.compile(r"(black|white|yellow|blue|green|brown|orange|spotted|striped)", re.IGNORECASE)
