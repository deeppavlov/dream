import json
import logging
import random
import os
import re
import en_core_web_sm
import inflect
import sentry_sdk
from CoBotQA.cobotqa_service import send_cobotqa
from enum import Enum, auto

import common.dialogflow_framework.stdm.dialogflow_extention as dialogflow_extention
import common.dialogflow_framework.utils.state as state_utils
from common.universal_templates import if_lets_chat_about_topic, COMPILE_WHAT_TO_TALK_ABOUT
from common.greeting import GREETING_QUESTIONS
from common.utils import get_intents, is_yes, is_no
from common.animals import PETS_TEMPLATE, COLORS_TEMPLATE, LIKE_ANIMALS_REQUESTS, OFFER_TALK_ABOUT_ANIMALS, \
    WILD_ANIMALS, WHAT_PETS_I_HAVE, CATS_DOGS_PHRASES

import dialogflows.scopes as scopes

sentry_sdk.init(os.getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

nlp = en_core_web_sm.load()
p = inflect.engine()

breeds = json.load(open("breeds.json", 'r'))

CONF_1 = 1.0
CONF_2 = 0.98
CONF_3 = 0.96
CONF_4 = 0.9
CONF_5 = 0.85

ANIMALS_TEMPLATE = re.compile(r"(animals|pets)", re.IGNORECASE)
COMPILE_GREETING_QUESTIONS = re.compile("|".join(GREETING_QUESTIONS["what_to_talk_about"]), re.IGNORECASE)


class State(Enum):
    USR_START = auto()
    #
    SYS_HAVE_PETS = auto()
    SYS_LIKE_ANIMALS = auto()
    SYS_WHAT_ANIMALS = auto()
    SYS_Q_HAVE_PETS = auto()
    SYS_ASK_ABOUT_ZOO = auto()
    SYS_ASK_SOME_QUESTIONS = auto()
    SYS_MENTION_ANIMALS = auto()
    #
    USR_WHAT_ANIMALS = auto()
    USR_TELL_ABOUT_PETS = auto()
    USR_ASK_ABOUT_ZOO = auto()
    USR_HAVE_PETS = auto()
    USR_ASK_SOME_QUESTIONS = auto()
    USR_MENTION_ANIMALS = auto()
    #
    SYS_IS_DOG_CAT = auto()
    SYS_IS_WILD = auto()
    SYS_WHAT_WILD = auto()
    SYS_WHY_DO_YOU_LIKE = auto()
    SYS_ASK_ABOUT_NAME = auto()
    SYS_NOT_HAVE = auto()
    SYS_ASK_ABOUT_BREED = auto()
    SYS_ASK_ABOUT_COLOR = auto()
    SYS_ASK_ABOUT_FEEDING = auto()
    SYS_USER_HAS_BEEN = auto()
    SYS_USER_HAS_NOT_BEEN = auto()
    #
    USR_ASK_ABOUT_DOG_CAT = auto()
    USR_ASK_ABOUT_NAME = auto()
    #
    USR_TELL_FACT_ASK_ABOUT_PETS = auto()
    USR_WHY_DO_YOU_LIKE = auto()
    USR_NOT_HAVE = auto()
    USR_WHAT_WILD = auto()
    USR_ASK_ABOUT_BREED = auto()
    USR_ASK_ABOUT_COLOR = auto()
    USR_ASK_ABOUT_FEEDING = auto()
    USR_ASK_MORE_DETAILS = auto()
    USR_SUGGEST_VISITING = auto()
    #
    SYS_TELL_FACT_ABOUT_BREED = auto()
    SYS_ASK_ABOUT_TRAINING = auto()
    #
    USR_TELL_FACT_ABOUT_BREED = auto()
    USR_ASK_ABOUT_TRAINING = auto()
    #
    SYS_ERR = auto()
    USR_ERR = auto()


def plural_nouns(text):
    plural_text = text
    try:
        processed_text = nlp(text)
        processed_tokens = []
        for token in processed_text:
            if token.tag_ == "NNP":
                processed_tokens.append(p.plural_noun(token))
            else:
                processed_tokens.append(token)
        plural_text = " ".join(processed_tokens)
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
    return plural_text


def lets_talk_about_request(vars):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    user_lets_chat_about = "lets_chat_about" in get_intents(user_uttr, which="intent_catcher") or \
                           if_lets_chat_about_topic(user_uttr["text"]) or re.search(COMPILE_WHAT_TO_TALK_ABOUT,
                                                                                    bot_uttr["text"]) or re.search(
        COMPILE_GREETING_QUESTIONS, bot_uttr["text"])
    user_lets_chat_about_animals = re.search(ANIMALS_TEMPLATE, user_uttr["text"]) and not \
        re.search("like|love|have", user_uttr["text"])
    linkto_talk_about_animals = any([req.lower() in bot_uttr["text"].lower()
                                     for req in OFFER_TALK_ABOUT_ANIMALS])

    user_agrees = is_yes(state_utils.get_last_human_utterance(vars))

    if (user_lets_chat_about and user_lets_chat_about_animals) or (linkto_talk_about_animals and user_agrees) or \
            re.findall(r"^(pets|animals)\??$", user_uttr["text"]):
        flag = True
    logger.info(f"lets_talk_about_request={flag}")
    return flag


def extract_pet(utt):
    fnd1 = re.findall(r"(used to )?(have|had|like) (a )?(cat|dog)s?", utt)
    fnd2 = re.findall(r"^(a )?(cat|dog)", utt)
    if fnd1:
        pet = fnd1[0][3]
    elif fnd2:
        pet = fnd2[0][1]
    else:
        pet = ""
    return pet


def retrieve_and_save(vars):
    text = state_utils.get_last_human_utterance(vars)["text"]
    shared_memory = state_utils.get_shared_memory(vars)
    found_users_pet = shared_memory.get("users_pet", "")
    if not found_users_pet:
        found_users_pet = extract_pet(text)
        if found_users_pet:
            state_utils.save_to_shared_memory(vars, users_pet=found_users_pet)
    return found_users_pet


def retrieve_and_save_name(vars):
    name = ""
    annotations = state_utils.get_last_human_utterance(vars)["annotations"]
    ner = annotations.get("ner", [])
    for entities in ner:
        if entities:
            for entity in entities:
                if entity.get("type", "") == "PER":
                    name = entity["text"]
                    state_utils.save_to_shared_memory(vars, users_pet_name=name)
    return name


def have_pets_request(ngrams, vars):
    flag = False
    text = state_utils.get_last_human_utterance(vars)["text"]
    if re.findall("(do|did) you have (any )?(pets|animals)", text):
        flag = True
    logger.info(f"have_pets_request={flag}")
    return flag


def like_animals_request(ngrams, vars):
    flag = False
    text = state_utils.get_last_human_utterance(vars)["text"]
    if re.findall("(do|did) you (like|love) (pets|animals)", text):
        flag = True
    logger.info(f"like_animals_request={flag}")
    return flag


def mention_animals_request(ngrams, vars):
    flag = False
    annotations = state_utils.get_last_human_utterance(vars)["annotations"]
    conceptnet = annotations.get("conceptnet", {})
    for elem, triplets in conceptnet.items():
        if "SymbolOf" in triplets:
            objects = triplets["SymbolOf"]
            if "animal" in objects:
                flag = True
    logger.info(f"mention_animals_request={flag}")
    return flag


def sys_what_animals_request(ngrams, vars):
    flag = False
    linkto_like_animals = any([req.lower() in state_utils.get_last_bot_utterance(vars)["text"].lower()
                               for req in LIKE_ANIMALS_REQUESTS])
    text = state_utils.get_last_human_utterance(vars)["text"]
    user_agrees = is_yes(state_utils.get_last_human_utterance(vars))
    shared_memory = state_utils.get_shared_memory(vars)
    if (not shared_memory.get("what_animals", False) and lets_talk_about_request(vars)) or \
            (linkto_like_animals and user_agrees) or text in {"animals", "pets"}:
        flag = True
    if flag:
        flag = random.choice([True, False])
        if not flag:
            logger.info("sys_what_animals_request not chosen")
    logger.info(f"sys_what_animals_request={flag}")
    return flag


def sys_have_pets_request(ngrams, vars):
    flag = False
    shared_memory = state_utils.get_shared_memory(vars)
    if not shared_memory.get("have_pets", False) and lets_talk_about_request(vars):
        flag = True
    logger.info(f"sys_have_pets_request={flag}")
    return flag


def sys_ask_about_zoo_request(ngrams, vars):
    flag = False
    shared_memory = state_utils.get_shared_memory(vars)
    if not shared_memory.get("ask_about_zoo", False) and (
            lets_talk_about_request(vars) or shared_memory.get("why_do_you_like", False)):
        flag = True
    logger.info(f"sys_ask_about_zoo_request={flag}")
    return flag


def sys_ask_some_questions_request(ngrams, vars):
    flag = False
    shared_memory = state_utils.get_shared_memory(vars)
    if not shared_memory.get("some_questions", False) and lets_talk_about_request(vars):
        flag = True
    logger.info(f"sys_ask_some_questions_request={flag}")
    return flag


def what_animals_response(vars):
    what_i_like = random.choice(WILD_ANIMALS)
    response = f"{what_i_like} What animals do you like?"
    state_utils.save_to_shared_memory(vars, what_animals=True)
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars)
    return response


def have_pets_response(vars):
    what_pets_i_have = random.choice(WHAT_PETS_I_HAVE)
    response = f"{what_pets_i_have} Do you have any pets?"
    state_utils.save_to_shared_memory(vars, have_pets=True)
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars)
    return response


def ask_about_zoo_response(vars):
    i_went_zoo = "Last weekend I went to the zoo with my family. We had a great day."
    question_zoo = "When have you been to the zoo last time?"
    response = " ".join([i_went_zoo, question_zoo])
    state_utils.save_to_shared_memory(vars, ask_about_zoo=True)
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars)
    return response


def ask_some_questions_response(vars):
    questions = ["Do you think that animals dream?", "Have you ever been in the farm?"]
    response = random.choice(questions)
    state_utils.save_to_shared_memory(vars, some_questions=True)
    state_utils.set_confidence(vars, confidence=CONF_2)
    return response


def tell_about_pets_response(vars):
    response = random.choice(WHAT_PETS_I_HAVE)
    state_utils.set_confidence(vars, confidence=CONF_1)
    return response


def mention_animals_response(vars):
    text = state_utils.get_last_human_utterance(vars)["text"]
    pet = re.findall(PETS_TEMPLATE, text)
    if pet:
        response = f"Do you have a {pet}?"
    else:
        response = "Do you have pets?"
    state_utils.set_confidence(vars, confidence=CONF_5)
    state_utils.set_can_continue(vars)
    return response


def user_has_been_request(ngrams, vars):
    flag = False
    if not is_no(state_utils.get_last_human_utterance(vars)):
        flag = True
    logger.info(f"user_has_been_request={flag}")
    return flag


def user_has_not_been_request(ngrams, vars):
    flag = False
    if is_no(state_utils.get_last_human_utterance(vars)):
        flag = True
    logger.info(f"user_has_not_been_request={flag}")
    return flag


def is_wild_request(ngrams, vars):
    flag = False
    text = state_utils.get_last_human_utterance(vars)["text"]
    if not re.findall(PETS_TEMPLATE, text):
        flag = True
    shared_memory = state_utils.get_shared_memory(vars)
    used_is_wild = shared_memory.get("tell_fact_ask_about_pets", False)
    used_why = shared_memory.get("why_do_you_like", False)
    if not used_why and not used_is_wild and flag:
        flag = random.choice([True, False])
    if used_is_wild:
        flag = False
    logger.info(f"is_wild_request={flag}")
    return flag


def why_do_you_like_request(ngrams, vars):
    flag = True
    text = state_utils.get_last_human_utterance(vars)["text"]
    if re.findall(PETS_TEMPLATE, text):
        flag = False
    shared_memory = state_utils.get_shared_memory(vars)
    used_why = shared_memory.get("why_do_you_like", False)
    if used_why:
        flag = False
    logger.info(f"why_do_you_like_request={flag}")
    return flag


def is_dog_cat_request(ngrams, vars):
    flag = False
    text = state_utils.get_last_human_utterance(vars)["text"]
    if re.findall(r"\b(cat|dog)s?\b", text) and not re.findall(r"\b(have|had)\b", text):
        flag = True
    logger.info(f"is_dog_cat_request={flag}")
    return flag


def ask_about_name_request(ngrams, vars):
    flag = False
    text = state_utils.get_last_human_utterance(vars)["text"]
    if re.findall(PETS_TEMPLATE, text) and not re.findall(r"(name|call)", text):
        flag = True
    logger.info(f"ask_about_name_request={flag}")
    return flag


def not_have_pets_request(ngrams, vars):
    flag = False
    text = state_utils.get_last_human_utterance(vars)["text"]
    if re.findall(r"(\bno\b|\bnot\b|don't)", text):
        flag = True
    logger.info(f"do_not_have_pets_request={flag}")
    return flag


def ask_about_breed_request(ngrams, vars):
    flag = False
    text = state_utils.get_last_human_utterance(vars)["text"]
    shared_memory = state_utils.get_shared_memory(vars)
    found_pet = re.findall(PETS_TEMPLATE, text)
    asked_name = shared_memory.get("asked_name", False)
    found_breed = re.findall("|".join(breeds.keys()), text)
    isno = is_no(state_utils.get_last_human_utterance(vars))
    logger.info(f"ask_about_breed_request_isno {isno}")
    if (found_pet or asked_name) and not found_breed and not isno:
        flag = True
    if flag and random.random() < 0.6:
        flag = False
        if not flag:
            logger.info("ask_about_breed_request not chosen")
    logger.info(f"ask_about_breed_request={flag}")
    return flag


def ask_about_color_request(ngrams, vars):
    flag = False
    text = state_utils.get_last_human_utterance(vars)["text"]
    shared_memory = state_utils.get_shared_memory(vars)
    found_pet = re.findall(PETS_TEMPLATE, text)
    asked_name = shared_memory.get("asked_name", False)
    found_color = re.findall(COLORS_TEMPLATE, text)
    isno = is_no(state_utils.get_last_human_utterance(vars))
    logger.info(f"ask_about_color_request_isno {isno}")
    if (found_pet or asked_name) and not found_color and not isno:
        flag = True
    logger.info(f"ask_about_color_request={flag}")
    return flag


def ask_about_feeding_request(ngrams, vars):
    flag = False
    text = state_utils.get_last_human_utterance(vars)["text"]
    if re.findall(PETS_TEMPLATE, text) and "feed" not in text:
        flag = True
    logger.info(f"ask_about_feeding_request={flag}")
    return flag


def ask_more_details_response(vars):
    response = "What is your impression? What did you like most?"
    state_utils.set_confidence(vars, confidence=CONF_1)
    return response


def suggest_visiting_response(vars):
    response = "A day at the zoo also encourages a healthy lifestyle while bringing family and friends together." + \
               "It is the perfect day trip destination for any season!"
    state_utils.set_confidence(vars, confidence=CONF_3)
    return response


def tell_fact_ask_about_pets_response(vars):
    annotations = state_utils.get_last_human_utterance(vars)["annotations"]
    nounphr = annotations.get("cobot_nounphrases", [])
    fact = ""
    if nounphr:
        fact = send_cobotqa(f"fact about {nounphr[0]}")
    ask_about_pets = "Do you have pets?"
    response = " ".join([fact, ask_about_pets])
    state_utils.save_to_shared_memory(vars, tell_fact_ask_about_pets=True)
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars)
    return response


def why_do_you_like_response(vars):
    annotations = state_utils.get_last_human_utterance(vars)["annotations"]
    conceptnet = annotations.get("conceptnet", {})
    found_animal = ""
    for elem, triplets in conceptnet.items():
        if "SymbolOf" in triplets:
            objects = triplets["SymbolOf"]
            if "animal" in objects:
                found_animal = elem
                found_animal = plural_nouns(found_animal)
    if found_animal:
        response = f"Cool! Why do you like {found_animal}?"
    else:
        response = f"Cool! Why do you like them?"
    state_utils.save_to_shared_memory(vars, why_do_you_like=True)
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars)
    return response


def ask_about_dog_cat_response(vars):
    found_users_pet = retrieve_and_save(vars)
    if found_users_pet:
        pet_phrase = random.choice(CATS_DOGS_PHRASES[found_users_pet])
        response = f"{pet_phrase} Do you have a {found_users_pet}?"
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars)
    return response


def has_pet_request(ngrams, vars):
    flag = False
    if not is_no(state_utils.get_last_human_utterance(vars)):
        flag = True
    logger.info(f"has_pet_request={flag}")
    return flag


def what_wild_request(ngrams, vars):
    flag = True
    shared_memory = state_utils.get_shared_memory(vars)
    if shared_memory.get("tell_fact_ask_about_pets", False):
        flag = False
    logger.info(f"what_wild_request={flag}")
    return flag


def ask_about_name_response(vars):
    found_users_pet = retrieve_and_save(vars)
    if found_users_pet:
        pet_phrase = random.choice(CATS_DOGS_PHRASES[found_users_pet])
        response = f"{pet_phrase} What is your {found_users_pet}'s name?"
    else:
        response = "What is his name?"
    state_utils.save_to_shared_memory(vars, asked_name=True)
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars)
    return response


def suggest_pet_response(vars):
    phrases = [phrase for pet_phrases in CATS_DOGS_PHRASES.values() for phrase in pet_phrases]
    pet_phrase = random.choice(phrases)
    response = f"{pet_phrase} Have you been to the zoo?"
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars)
    return response


def ask_about_breed_response(vars):
    found_users_pet = retrieve_and_save(vars)
    found_users_pet_name = retrieve_and_save_name(vars)
    if found_users_pet:
        pet_phrase = random.choice(CATS_DOGS_PHRASES[found_users_pet])
        if found_users_pet_name:
            response = f"{pet_phrase} What breed is {found_users_pet_name}?"
        else:
            response = f"{pet_phrase} What breed is your {found_users_pet}?"
    else:
        response = "What breed is it?"
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars)
    return response


def ask_about_color_response(vars):
    found_users_pet = retrieve_and_save(vars)
    found_users_pet_name = retrieve_and_save_name(vars)
    if found_users_pet:
        pet_phrase = random.choice(CATS_DOGS_PHRASES[found_users_pet])
        if found_users_pet_name:
            response = f"{pet_phrase} What color is {found_users_pet_name}?"
        else:
            response = f"{pet_phrase} What color is your {found_users_pet}?"
    else:
        response = "What color is it?"
    state_utils.set_confidence(vars, confidence=CONF_1)
    return response


def what_wild_response(vars):
    what_i_like = random.choice(WILD_ANIMALS)
    response = f"{what_i_like} What wild animals do you like?"
    state_utils.save_to_shared_memory(vars, what_animals=True)
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars)
    return response


def ask_about_feeding_response(vars):
    response = "How do you feed him?"
    state_utils.set_confidence(vars, confidence=CONF_4)
    return response


def tell_fact_about_breed_request(ngrams, vars):
    flag = False
    text = state_utils.get_last_human_utterance(vars)["text"]
    if re.findall("|".join(breeds.keys()), text):
        flag = True
    logger.info(f"tell_fact_about_breed_request={flag}")
    return flag


def ask_about_training_request(ngrams, vars):
    flag = True
    if is_no(state_utils.get_last_human_utterance(vars)):
        flag = False
    logger.info(f"ask_about_training_request={flag}")
    return flag


def tell_fact_about_breed_response(vars):
    annotations = state_utils.get_last_human_utterance(vars)["annotations"]
    nounphrases = annotations.get("cobot_nounphrases")
    fact = ""
    for nounphrase in nounphrases:
        if nounphrase in breeds:
            fact = breeds[nounphrase]
            break
    if fact:
        response = fact
    else:
        response = "They are sensitive and intelligent, known for undying loyalty and the amazing ability to" + \
                   "foresee their owners’ needs."
    state_utils.save_to_shared_memory(vars, tell_fact_about_breed=True)
    shared_memory = state_utils.get_shared_memory(vars)
    if not shared_memory.get("ask_about_zoo", False):
        response = f"{response} Have you been to the zoo?"
    state_utils.set_confidence(vars, confidence=CONF_1)
    return response


def ask_about_training_response(vars):
    response = "Did you train him to execute commands?"
    state_utils.set_confidence(vars, confidence=CONF_4)
    return response


def error_response(vars):
    state_utils.set_confidence(vars, 0)
    return ""


simplified_dialog_flow = dialogflow_extention.DFEasyFilling(State.USR_START)

simplified_dialog_flow.add_user_serial_transitions(
    State.USR_START,
    {
        State.SYS_WHAT_ANIMALS: sys_what_animals_request,
        State.SYS_Q_HAVE_PETS: sys_have_pets_request,
        State.SYS_ASK_ABOUT_ZOO: sys_ask_about_zoo_request,
        State.SYS_ASK_SOME_QUESTIONS: sys_ask_some_questions_request,
        State.SYS_HAVE_PETS: have_pets_request,
        State.SYS_LIKE_ANIMALS: like_animals_request,
        State.SYS_ASK_ABOUT_BREED: ask_about_breed_request,
        State.SYS_ASK_ABOUT_COLOR: ask_about_color_request,
        State.SYS_MENTION_ANIMALS: mention_animals_request,
    },
)
simplified_dialog_flow.set_error_successor(State.USR_START, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.SYS_WHAT_ANIMALS, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.SYS_Q_HAVE_PETS, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.SYS_ASK_ABOUT_ZOO, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.SYS_ASK_SOME_QUESTIONS, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.SYS_MENTION_ANIMALS, State.SYS_ERR)

simplified_dialog_flow.add_system_transition(
    State.SYS_WHAT_ANIMALS,
    State.USR_WHAT_ANIMALS,
    what_animals_response,
)
simplified_dialog_flow.add_system_transition(
    State.SYS_Q_HAVE_PETS,
    State.USR_HAVE_PETS,
    have_pets_response,
)
simplified_dialog_flow.add_system_transition(
    State.SYS_ASK_ABOUT_ZOO,
    State.USR_ASK_ABOUT_ZOO,
    ask_about_zoo_response,
)
simplified_dialog_flow.add_system_transition(
    State.SYS_ASK_SOME_QUESTIONS,
    State.USR_ASK_SOME_QUESTIONS,
    ask_some_questions_response,
)

simplified_dialog_flow.add_system_transition(
    State.SYS_HAVE_PETS,
    State.USR_TELL_ABOUT_PETS,
    tell_about_pets_response,
)
simplified_dialog_flow.set_error_successor(State.SYS_HAVE_PETS, State.SYS_ERR)

simplified_dialog_flow.add_system_transition(
    State.SYS_MENTION_ANIMALS,
    State.USR_MENTION_ANIMALS,
    mention_animals_response,
)
simplified_dialog_flow.set_error_successor(State.USR_MENTION_ANIMALS, State.SYS_ERR)

simplified_dialog_flow.add_system_transition(
    State.SYS_LIKE_ANIMALS,
    State.USR_TELL_ABOUT_PETS,
    tell_about_pets_response,
)
simplified_dialog_flow.set_error_successor(State.SYS_LIKE_ANIMALS, State.SYS_ERR)

simplified_dialog_flow.add_user_serial_transitions(
    State.USR_WHAT_ANIMALS,
    {
        State.SYS_IS_DOG_CAT: is_dog_cat_request,
        State.SYS_IS_WILD: is_wild_request,
        State.SYS_WHY_DO_YOU_LIKE: why_do_you_like_request,
        State.SYS_ASK_ABOUT_BREED: ask_about_breed_request,
        State.SYS_ASK_ABOUT_COLOR: ask_about_color_request,
        State.SYS_ASK_ABOUT_FEEDING: ask_about_feeding_request,
        State.SYS_HAVE_PETS: have_pets_request,
        State.SYS_LIKE_ANIMALS: like_animals_request,
    },
)
simplified_dialog_flow.set_error_successor(State.USR_WHAT_ANIMALS, State.SYS_ERR)

simplified_dialog_flow.add_user_serial_transitions(
    State.USR_HAVE_PETS,
    {
        State.SYS_IS_WILD: is_wild_request,
        State.SYS_ASK_ABOUT_NAME: ask_about_name_request,
        State.SYS_NOT_HAVE: not_have_pets_request,
        State.SYS_ASK_ABOUT_BREED: ask_about_breed_request,
        State.SYS_ASK_ABOUT_COLOR: ask_about_color_request,
        State.SYS_ASK_ABOUT_FEEDING: ask_about_feeding_request,
        State.SYS_HAVE_PETS: have_pets_request,
        State.SYS_LIKE_ANIMALS: like_animals_request,
    },
)
simplified_dialog_flow.set_error_successor(State.USR_HAVE_PETS, State.SYS_ERR)

simplified_dialog_flow.add_user_serial_transitions(
    State.USR_TELL_ABOUT_PETS,
    {
        State.SYS_IS_WILD: is_wild_request,
        State.SYS_ASK_ABOUT_BREED: ask_about_breed_request,
        State.SYS_ASK_ABOUT_COLOR: ask_about_color_request,
        State.SYS_ASK_ABOUT_FEEDING: ask_about_feeding_request,
    },
)
simplified_dialog_flow.set_error_successor(State.USR_TELL_ABOUT_PETS, State.SYS_ERR)

simplified_dialog_flow.add_user_serial_transitions(
    State.USR_ASK_ABOUT_ZOO,
    {
        State.SYS_USER_HAS_BEEN: user_has_been_request,
        State.SYS_USER_HAS_NOT_BEEN: user_has_not_been_request,
        State.SYS_HAVE_PETS: have_pets_request,
        State.SYS_LIKE_ANIMALS: like_animals_request,
    },
)
simplified_dialog_flow.set_error_successor(State.USR_ASK_ABOUT_ZOO, State.SYS_ERR)

simplified_dialog_flow.add_system_transition(
    State.SYS_USER_HAS_BEEN,
    State.USR_ASK_MORE_DETAILS,
    ask_more_details_response,
)
simplified_dialog_flow.set_error_successor(State.SYS_USER_HAS_BEEN, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.USR_ASK_MORE_DETAILS, State.SYS_ERR)

simplified_dialog_flow.add_system_transition(
    State.SYS_USER_HAS_NOT_BEEN,
    State.USR_SUGGEST_VISITING,
    suggest_visiting_response,
)
simplified_dialog_flow.set_error_successor(State.SYS_USER_HAS_NOT_BEEN, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.USR_SUGGEST_VISITING, State.SYS_ERR)

simplified_dialog_flow.add_system_transition(
    State.SYS_NOT_HAVE,
    State.USR_NOT_HAVE,
    suggest_pet_response,
)
simplified_dialog_flow.set_error_successor(State.SYS_NOT_HAVE, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.USR_NOT_HAVE, State.SYS_ERR)

simplified_dialog_flow.add_system_transition(
    State.SYS_IS_DOG_CAT,
    State.USR_ASK_ABOUT_DOG_CAT,
    ask_about_dog_cat_response,
)
simplified_dialog_flow.set_error_successor(State.SYS_IS_DOG_CAT, State.SYS_ERR)

simplified_dialog_flow.add_user_serial_transitions(
    State.USR_NOT_HAVE,
    {
        State.SYS_USER_HAS_BEEN: user_has_been_request,
        State.SYS_USER_HAS_NOT_BEEN: user_has_not_been_request,
    },
)
simplified_dialog_flow.add_user_serial_transitions(
    State.USR_ASK_ABOUT_DOG_CAT,
    {
        State.SYS_ASK_ABOUT_BREED: has_pet_request,
        State.SYS_ASK_ABOUT_COLOR: has_pet_request,
        State.SYS_WHAT_WILD: what_wild_request,
    },
)
simplified_dialog_flow.set_error_successor(State.USR_ASK_ABOUT_DOG_CAT, State.SYS_ERR)

simplified_dialog_flow.add_system_transition(
    State.SYS_WHAT_WILD,
    State.USR_WHAT_WILD,
    what_wild_response,
)
simplified_dialog_flow.set_error_successor(State.SYS_WHAT_WILD, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.USR_WHAT_WILD, State.SYS_ERR)

simplified_dialog_flow.add_user_serial_transitions(
    State.USR_WHAT_WILD,
    {
        State.SYS_WHY_DO_YOU_LIKE: why_do_you_like_request,
    },
)

simplified_dialog_flow.add_system_transition(
    State.SYS_IS_WILD,
    State.USR_TELL_FACT_ASK_ABOUT_PETS,
    tell_fact_ask_about_pets_response,
)
simplified_dialog_flow.set_error_successor(State.SYS_IS_WILD, State.SYS_ERR)

simplified_dialog_flow.add_system_transition(
    State.SYS_WHY_DO_YOU_LIKE,
    State.USR_WHY_DO_YOU_LIKE,
    why_do_you_like_response,
)
simplified_dialog_flow.set_error_successor(State.SYS_WHY_DO_YOU_LIKE, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.USR_WHY_DO_YOU_LIKE, State.SYS_ERR)
simplified_dialog_flow.add_system_transition(
    State.SYS_ASK_ABOUT_NAME,
    State.USR_ASK_ABOUT_NAME,
    ask_about_name_response,
)
simplified_dialog_flow.set_error_successor(State.SYS_ASK_ABOUT_NAME, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.USR_ASK_ABOUT_NAME, State.SYS_ERR)
simplified_dialog_flow.add_system_transition(
    State.SYS_ASK_ABOUT_BREED,
    State.USR_ASK_ABOUT_BREED,
    ask_about_breed_response,
)
simplified_dialog_flow.set_error_successor(State.SYS_ASK_ABOUT_BREED, State.SYS_ERR)

simplified_dialog_flow.add_system_transition(
    State.SYS_ASK_ABOUT_COLOR,
    State.USR_ASK_ABOUT_COLOR,
    ask_about_color_response,
)
simplified_dialog_flow.set_error_successor(State.SYS_ASK_ABOUT_COLOR, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.USR_ASK_ABOUT_COLOR, State.SYS_ERR)

simplified_dialog_flow.add_system_transition(
    State.SYS_ASK_ABOUT_FEEDING,
    State.USR_ASK_ABOUT_FEEDING,
    ask_about_feeding_response,
)
simplified_dialog_flow.set_error_successor(State.SYS_ASK_ABOUT_FEEDING, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.USR_ASK_ABOUT_FEEDING, State.SYS_ERR)

simplified_dialog_flow.add_user_serial_transitions(
    State.USR_ASK_ABOUT_NAME,
    {
        State.SYS_ASK_ABOUT_BREED: ask_about_breed_request,
        State.SYS_ASK_ABOUT_COLOR: ask_about_color_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    State.USR_WHY_DO_YOU_LIKE,
    {
        State.SYS_Q_HAVE_PETS: sys_have_pets_request,
        State.SYS_ASK_ABOUT_ZOO: sys_ask_about_zoo_request,
    },
)
simplified_dialog_flow.add_user_serial_transitions(
    State.USR_ASK_ABOUT_BREED,
    {
        State.SYS_TELL_FACT_ABOUT_BREED: tell_fact_about_breed_request,
        State.SYS_ASK_ABOUT_TRAINING: ask_about_training_request,
        State.SYS_HAVE_PETS: have_pets_request,
        State.SYS_LIKE_ANIMALS: like_animals_request,
    },
)
simplified_dialog_flow.set_error_successor(State.USR_ASK_ABOUT_BREED, State.SYS_ERR)

simplified_dialog_flow.add_system_transition(
    State.SYS_TELL_FACT_ABOUT_BREED,
    State.USR_TELL_FACT_ABOUT_BREED,
    tell_fact_about_breed_response,
)
simplified_dialog_flow.set_error_successor(State.SYS_TELL_FACT_ABOUT_BREED, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.USR_TELL_FACT_ABOUT_BREED, State.SYS_ERR)

simplified_dialog_flow.add_system_transition(
    State.SYS_ASK_ABOUT_TRAINING,
    State.USR_ASK_ABOUT_TRAINING,
    ask_about_training_response,
)
simplified_dialog_flow.set_error_successor(State.SYS_ASK_ABOUT_TRAINING, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.USR_ASK_ABOUT_TRAINING, State.SYS_ERR)

# cycle transitions to State.SYS_HAVE_PETS

simplified_dialog_flow.add_user_serial_transitions(
    State.USR_TELL_FACT_ASK_ABOUT_PETS,
    {
        State.SYS_ASK_ABOUT_NAME: ask_about_name_request,
        State.SYS_NOT_HAVE: not_have_pets_request,
        State.SYS_ASK_ABOUT_BREED: ask_about_breed_request,
        State.SYS_ASK_ABOUT_COLOR: ask_about_color_request,
        State.SYS_LIKE_ANIMALS: like_animals_request,
    },
)
simplified_dialog_flow.add_user_serial_transitions(
    State.USR_ASK_ABOUT_COLOR,
    {
        State.SYS_ASK_ABOUT_ZOO: sys_ask_about_zoo_request,
        State.SYS_HAVE_PETS: have_pets_request,
        State.SYS_LIKE_ANIMALS: like_animals_request,
    },
)
simplified_dialog_flow.add_user_serial_transitions(
    State.USR_ASK_ABOUT_FEEDING,
    {
        State.SYS_HAVE_PETS: have_pets_request,
        State.SYS_LIKE_ANIMALS: like_animals_request,
    },
)
simplified_dialog_flow.add_user_serial_transitions(
    State.USR_TELL_FACT_ABOUT_BREED,
    {
        State.SYS_USER_HAS_BEEN: user_has_been_request,
        State.SYS_USER_HAS_NOT_BEEN: user_has_not_been_request,
    },
)

# cycle transitions to State.SYS_LIKE_ANIMALS

simplified_dialog_flow.add_user_transition(
    State.USR_ASK_SOME_QUESTIONS,
    State.SYS_LIKE_ANIMALS,
    like_animals_request,
)

simplified_dialog_flow.add_system_transition(
    State.SYS_ERR,
    (scopes.MAIN, scopes.State.USR_ROOT),
    error_response,
)

dialogflow = simplified_dialog_flow.get_dialogflow()
