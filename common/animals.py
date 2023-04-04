import re
from common.universal_templates import is_any_question_sentence_in_utterance, NOT_LIKE_PATTERN
from common.utils import get_topics, TOPIC_GROUPS, get_comet_conceptnet_annotations

LIKE_ANIMALS_REQUESTS = ["Do you like animals?"]
HAVE_PETS_REQUESTS = ["Do you have pets?"]

OFFER_TALK_ABOUT_ANIMALS = [
    "Would you like to talk about animals?",
    "Let's chat about animals. Do you agree?",
    "I'd like to talk about animals, would you?",
    "I think that pets are a great source of entertainment. Do you have pets at home?",
    "We all know that pets are remarkable for their capacity to love. Do you have pets " "at home?",
]

TRIGGER_PHRASES = LIKE_ANIMALS_REQUESTS + HAVE_PETS_REQUESTS + OFFER_TALK_ABOUT_ANIMALS


def skill_trigger_phrases():
    return TRIGGER_PHRASES


def animals_skill_was_proposed(prev_bot_utt):
    return any([phrase.lower() in prev_bot_utt.get("text", "").lower() for phrase in TRIGGER_PHRASES])


ANIMALS_TEMPLATE = re.compile(r"(animal|\bpet\b|\bpets\b)", re.IGNORECASE)
ANIMAL_MENTION_TEMPLATE = re.compile(r"animal", re.IGNORECASE)
PETS_TEMPLATE = re.compile(
    r"(\bcat\b|\bcats\b|\bdog\b|\bdogs\b|horse|puppy|puppies|kitty|kitties|kitten|parrot|"
    r"\brat\b|\brats\b|mouse|hamster|fish\b)",
    re.IGNORECASE,
)
PETS_TEMPLATE_EXT = re.compile(
    r"(\bcat\b|\bcats\b|\bdog\b|\bdogs\b|horse|puppy|puppies|kitty|kitties|kitten|parrot|"
    r"\brat\b|\brats\b|mouse|hamster|fish\b|bird)",
    re.IGNORECASE,
)
ANIMALS_FIND_TEMPLATE = re.compile(
    r"(animal|\bpet\b|\bpets|\bcat\b|\bcats\b|\bdog\b|\bdogs\b|horse|puppy|puppies|"
    r"kitty|kitties|kitten|parrot|\brat\b|\brats\b|mouse|hamster|fish(es)?\b)",
    re.IGNORECASE,
)
HAVE_LIKE_PETS_TEMPLATE = re.compile(
    r"(do|did|have) you (have |had |like )?(any |a )?(pets|pet|animals|animal)", re.IGNORECASE
)
HAVE_PETS_TEMPLATE = re.compile(r"(do|did|have) you (have |had )?(any |a )?(pets|pet|animals|animal)", re.IGNORECASE)
LIKE_PETS_TEMPLATE = re.compile(r"(do|did|have) you (like |love )?(any |a )?(pets|pet|animals|animal)", re.IGNORECASE)
DONT_LIKE = re.compile(r"(do not like|don't like|dont like|hate)", re.IGNORECASE)
DO_YOU_HAVE_TEMPLATE = re.compile(
    r"do you have (a |an |the |any |some )?(cat|dog|puppy|kitty|kitten|rat|fish|parrot" r"|hamster|\bpet|\bpets)",
    re.IGNORECASE,
)
NOT_SWITCH_TEMPLATE = re.compile(r"(hot dog|doja cat)", re.IGNORECASE)
ANIMAL_BADLIST = {"animal", "animals"}

breed_replace_dict = {"lab": "labrador"}
pet_games = {"dog": ["frisbee", "hide and seek"], "cat": ["run and fetch"]}
nounphr_from_questions = [
    "swim",
    "swimming",
    "bubbles",
    "gadgets",
    "tablet",
    "robot",
    "vacuum",
    "cleaner",
    "meat",
    "smell",
    "laptop",
    "trick",
    "ball",
    "palm",
    "five",
    "Android",
    "Ipad",
    "Instagram",
    "app",
    "screen",
]
fallbacks = [
    "Sorry, I have forgot about this, I have a bad memory. Let's continue our chat about pets.",
    "Sorry, I forgot the answer, but I would like to tell you more about pets.",
    "Oh, it's not my lucky day, I can't come up with the answer.",
    "Yesterday my neighbour was playing soccer and the ball hit my head, so today i'm a little dumb.",
]

re_tokenizer = re.compile(r"[\w']+|[^\w ]")


def check_about_animals(user_uttr):
    found_topics = get_topics(user_uttr, probs=False, which="all")
    if any([animal_topic in found_topics for animal_topic in TOPIC_GROUPS["animals"]]):
        return True
    elif re.findall(ANIMALS_FIND_TEMPLATE, user_uttr["text"]):
        return True
    else:
        return False


def mentioned_animal(annotations):
    flag = False
    conceptnet = get_comet_conceptnet_annotations({"annotations": annotations})
    for elem, triplets in conceptnet.items():
        if "SymbolOf" in triplets:
            objects = triplets["SymbolOf"]
            if "animal" in objects:
                flag = True
    return flag


def find_entity_by_types(annotations, types_to_find):
    found_entity_wp = ""
    wp_output = annotations.get("wiki_parser", {})
    types_to_find = set(types_to_find)
    if isinstance(wp_output, dict):
        entities_info = wp_output.get("animals_skill_entities_info", {})
        for entity, triplets in entities_info.items():
            types = (
                triplets.get("types", [])
                + triplets.get("instance of", [])
                + triplets.get("subclass of", [])
                + triplets.get("types_2_hop", [])
            )
            type_ids = [elem for elem, label in types]
            inters = set(type_ids).intersection(types_to_find)
            if inters:
                found_entity_wp = entity
                break
    return found_entity_wp


def find_entity_conceptnet(annotations, types_to_find):
    conceptnet = get_comet_conceptnet_annotations({"annotations": annotations})
    for elem, triplets in conceptnet.items():
        if "SymbolOf" in triplets:
            objects = triplets["SymbolOf"]
            if set(types_to_find).intersection(objects):
                found_entity = elem
                return found_entity
    return ""


def stop_about_animals(user_uttr, shared_memory):
    flag = False
    annotations = user_uttr["annotations"]
    cobot_entities = annotations.get("cobot_entities", {}).get("entities", [])
    found_nounphr_for_questions = False
    for entity in cobot_entities:
        entity_tokens = set(re.findall(re_tokenizer, entity))
        for nounphr in nounphr_from_questions:
            nounphr_tokens = set(re.findall(re_tokenizer, nounphr))
            if entity_tokens.intersection(nounphr_tokens):
                found_nounphr_for_questions = True
                break
        if found_nounphr_for_questions:
            break
    my_pet_name = shared_memory.get("my_pet_name", "").lower()
    user_pet_name = shared_memory.get("users_pet_name", "").lower()
    name_in_entities = my_pet_name in cobot_entities or user_pet_name in cobot_entities
    found_animal_substr = re.findall(ANIMALS_FIND_TEMPLATE, user_uttr["text"])
    is_stop = re.findall(r"(stop|shut|something else|change|don't want)", user_uttr["text"])
    found_animal_wp = find_entity_by_types(annotations, {"Q55983715", "Q16521", "Q43577", "Q39367", "Q38547"})
    isq = is_any_question_sentence_in_utterance(user_uttr)
    user_ask = re.findall(r"ask (you )?(a )?question", user_uttr["text"], re.IGNORECASE)
    dont_like = re.findall(NOT_LIKE_PATTERN, user_uttr["text"])
    if (
        (
            isq
            and cobot_entities
            and not name_in_entities
            and not found_animal_substr
            and not found_animal_wp
            and not found_nounphr_for_questions
        )
        or is_stop
        or user_ask
        or dont_like
    ):
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
    "I like eagles. Bald eagle is the symbol of America. A bald eagle has Superman-like vision.",
]

WHAT_PETS_I_HAVE = [
    {
        "pet": "dog",
        "name": "Jack",
        "breed": "German Shepherd",
        "sentence": "I have a dog named Jack. He is a German Shepherd. He is very cute.",
    },
    {
        "pet": "dog",
        "name": "Charlie",
        "breed": "Husky",
        "sentence": "I have a dog named Charlie. He is a Husky. He is very cute.",
    },
    {
        "pet": "dog",
        "name": "Archie",
        "breed": "Labrador",
        "sentence": "I have a dog named Archie. He is a Labrador. He is very cute.",
    },
    {
        "pet": "cat",
        "name": "Thomas",
        "breed": "Norwegian Forest cat",
        "sentence": "I have a cat named Thomas. He is a big fluffy Norwegian Forest cat.",
    },
    {"pet": "cat", "name": "Jackie", "breed": "Persian", "sentence": "I have a cat named Jackie. He is a Persian."},
    {"pet": "cat", "name": "Prince", "breed": "Siamese", "sentence": "I have a cat named Prince. He is a Siamese."},
]

CATS_DOGS_PHRASES = {
    "cat": [
        "Cats are a great choice of pet.",
        "Cats have long been one of the more popular companion animals, constantly battling dogs "
        "for the number one spot.",
    ],
    "dog": ["Dogs are a great choice of pet.", "It is almost impossible to feel lonely when your dog is by your side."],
}

MY_PET_FACTS = {
    "cat": [
        {
            "ack": "",
            "statement": "Sometimes when I'm working on my laptop, my cat sits on my keyboard.",
            "question": "Do you think it's annoying or maybe funny?",
        },
        {
            "ack": "",
            "statement": "My cat meows only when he is hungry but my dog barks very often.",
            "question": "Do you agree that cats are quiet pets?",
        },
        {
            "ack": "",
            "statement": "My cat and my dog are good friends but my dog does not like other cats.",
            "question": "What is your opinion, should a dog like all cats?",
        },
        {
            "ack": "",
            "statement": "My cat also likes playing on my tablet pc. You know, there are games for "
            "Android or Ipad with catching fish on screen and my cat slides his paws on the "
            "screen to catch fish.",
            "question": "Do you think that pets can use gadgets the same way as humans?",
        },
        {"ack": "", "statement": "", "question": "Do you think I should create an Instagram account for my cat?"},
        {
            "ack": "",
            "statement": "My cat does not let mice and rats go into my home.",
            "question": "Did you know that mice feel the smell of a cat and are afraid to approach the cat?",
        },
        {
            "ack": "",
            "statement": "Yesterday I played with my cat a game, i placed treat in hard-to-reach spot "
            "in my home and my cat retrieved it using his smell.",
            "question": "Do you think that cats have a good smell?",
        },
    ],
    "dog": [
        {
            "ack": "",
            "statement": "I walk with my dog every morning.",
            "question": "Do you think that having a dog help to stay active?",
        },
        {
            "ack": "",
            "statement": "My dog knows many tricks, for example a high five. I hold my palm out and as "
            "the dog hits my palm, give the command high five. My dog raises his paw and "
            "touches my open palm.",
            "question": "Do you think my dog is very smart?",
        },
        {
            "ack": "",
            "statement": "When I go swimming in the lake, my dog swims with me.",
            "question": "Do you like swimming?",
        },
        {
            "ack": "",
            "statement": "When an unfamiliar man comes into my house, my dog barks at him, and when I "
            "tell him stop he stops barking.",
            "question": "Do you think that a dog should bark at strangers or maybe bite them?",
        },
        {
            "ack": "",
            "statement": "When I look at my dog and yawn, sometimes my dog yawns too.",
            "question": "Is it funny?",
        },
        {
            "ack": "",
            "statement": "My dog likes to eat meat bones.",
            "question": "What do you think is better for feeding a dog — royal canin food or natural food?",
        },
        {
            "ack": "",
            "statement": "My dog likes to play with my robot vacuum cleaner.",
            "question": "Do you agree that a robot cleaner is also a pet?",
        },
        {
            "ack": "",
            "statement": "Playing with my dog is a lot of fun, I throw a tennis ball and he bounces off "
            "to retrieve it.",
            "question": "",
        },
    ],
}

USER_PETS_Q = [
    {"what": "name", "keywords": ["name", "call"], "attr": "users_pet_name"},
    {"what": "breed", "keywords": ["breed"], "attr": "users_pet_breed"},
    {"what": "play", "keywords": ["play"], "attr": ""},
    {"what": "like", "keywords": ["like", "love"], "attr": ""},
    {"what": "videos", "keywords": ["videos"], "attr": ""},
    {"what": "pandemic", "keywords": ["pandemic", "virus"], "attr": ""},
]

WILD_ANIMALS_Q = [
    {"ack": "", "statement": "I like {} very much.", "question": "Have you seen {} in wildlife?"},
    {"ack": "", "statement": "I like watching {} in the zoo.", "question": "Would you like to have pet {}?"},
    {
        "ack": "",
        "statement": "I saw interesting TV programs about {} on the channel Animal Planet.",
        "question": "Do you like to watch Discovery Channel?",
    },
]

ANIMALS_WIKI_Q = {
    "distribution": "Would you like to know where {} live?",
    "behavior": "I would like to tell you about behavior of {}, okay?",
    "behaviour": "I would like to tell you about behavior of {}, okay?",
    "cultural": "Do you want to hear about {} in popular culture?",
    "culture": "Do you want to hear about {} in popular culture?",
    "relationship with humans": "Would you like to hear about relationship of {} with humans?",
}

ANIMALS_COBOT_Q = [
    "Would you like to know more about {}?",
    "Do you want to hear more about {}?",
    "Should I continue?",
    "Do you want more details?",
    "What is your opinion?",
]
