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


ANIMALS_TEMPLATE = re.compile(r"(animal|\bpet\b|\bpets\b)", re.IGNORECASE)
PETS_TEMPLATE = re.compile(r"(\bcat\b|\bcats\b|\bdog\b|\bdogs\b|horse|puppy|kitty|kitten|parrot|\brat\b|\brats\b|"
                           r"mouse|hamster)", re.IGNORECASE)
ANIMALS_FIND_TEMPLATE = re.compile(r"(animal|\bpet\b|\bpets\b|\bcat\b|\bcats\b|\bdog\b|\bdogs\b|horse|puppy|kitty|"
                                   r"kitten|parrot|\brat\b|\brats\b|mouse|hamster)", re.IGNORECASE)
HAVE_LIKE_PETS_TEMPLATE = re.compile(r"(do|did|have) you (have |had |like )?(any |a )?(pets|pet|animals|animal)",
                                     re.IGNORECASE)
HAVE_PETS_TEMPLATE = re.compile(r"(do|did|have) you (have |had )?(any |a )?(pets|pet|animals|animal)", re.IGNORECASE)
LIKE_PETS_TEMPLATE = re.compile(r"(do|did|have) you (like |love )?(any |a )?(pets|pet|animals|animal)", re.IGNORECASE)


def check_about_animals(text):
    if re.findall(ANIMALS_FIND_TEMPLATE, text):
        return True
    else:
        return False


def mentioned_animal(annotations):
    flag = False
    conceptnet = annotations.get("conceptnet", {})
    for elem, triplets in conceptnet.items():
        if "SymbolOf" in triplets:
            objects = triplets["SymbolOf"]
            if "animal" in objects:
                flag = True
    return flag


COLORS_TEMPLATE = re.compile(r"(black|white|yellow|blue|green|brown|orange|spotted|striped)", re.IGNORECASE)

WILD_ANIMALS = [
    "I like squirrels. I admire how skillfully they can climb up trees. "
    "When I walk in the park, sometimes I feed squirrels.",
    "I like mountain goats. "
    "I saw a video on Youtube where a goat was climbing up a sheer cliff and they did not fall down.",
    "I like elephants. When I was in India, I rode an elephant.",
    "I like foxes. Foxes are intriguing animals, known for their intelligence, playfulness, and lithe athleticism.",
    "I like wolves. They are related to dogs. I love how they vary in fur color. I love how packs work together.",
    "I like eagles. Bald eagle is the symbol of America. A bald eagle has Superman-like vision."
]

WHAT_PETS_I_HAVE = [{"pet": "dog", "name": "Jack", "breed": "German Shepherd",
                     "sentence": "I have a dog named Jack. He is a German Shepherd. He is very cute."},
                    {"pet": "dog", "name": "Charlie", "breed": "Husky",
                     "sentence": "I have a dog named Charlie. He is a Husky. He is very cute."},
                    {"pet": "dog", "name": "Archie", "breed": "Labrador",
                     "sentence": "I have a dog named Archie. He is a Labrador. He is very cute."},
                    {"pet": "cat", "name": "Thomas", "breed": "Maine Coon",
                     "sentence": "I have a cat named Thomas. He is a big fluffy Maine Coon."},
                    {"pet": "cat", "name": "Jackie", "breed": "Persian",
                     "sentence": "I have a cat named Jackie. He is a Persian."},
                    {"pet": "cat", "name": "Prince", "breed": "Siamese",
                     "sentence": "I have a cat named Prince. He is a Siamese."}
                    ]

CATS_DOGS_PHRASES = {"cat": ["Can cats reduce stress and improve mood? The answer seems to be yes.",
                             "Cats have long been one of the more popular companion animals, constantly battling dogs "
                             "for the number one spot.",
                             "Whether you’ve had your cat for her whole life, or you’ve just welcomed a cat or kitten "
                             "into your new family, you can find yourself learning something new about your cat "
                             "everyday."],
                     "dog": ["Having a dog can help you stay active. Nothing beats a long walk with your "
                             "four-legged friend on a fresh, spring morning.",
                             "Nothing beats a long walk with your four-legged friend on a fresh, spring morning. "
                             "Or seeing the joy on their faces when you pick up a ball and they know it’s playtime "
                             "in the local park!",
                             "There’s an old saying, which is certainly true, that dogs repay the love you give "
                             "them ten-fold.",
                             "One of the most noticeable benefits of owning a dog is that it’s almost impossible to "
                             "feel lonely when your dog is by your side, and for good reason."]
                     }

MY_CAT = ["My cat is as frail as an autumn leaf as an autumn leaf but her purr is as loud as seas.",
          "Her claws are as gnarled as an ancient oak.",
          "She sits by the fire and tries to keep warm or she curls herself up on my knees.",
          "Her fur is as soft as a kitten's coat but her ears are as deaf as the breeze.",
          "He is beautiful and easy to care for, his medium white fur needs no extra brushing.",
          "Sometimes my cat thinks that she is a dog."]

MY_DOG = ["My dog is incredibly and unconditionally loyal to me. He loves me as much as I love him or sometimes more.",
          "We always play catch outside my house or sometimes in the park.",
          "He is the reason I am active and good at exercise. He will never let me be lazy. "
          "Whenever possible, we always keep playing some or the other games with him.",
          "He will play games with us, keep all our family members together with his love and cuddles and "
          "also he keeps thieves and uninvited guests out of our home.",
          "He is active and playful, enjoying games like fetch and learning tricks.",
          "Playing with him is a lot of fun, I throw a tennis ball and he bounces off to retrieve it."]
