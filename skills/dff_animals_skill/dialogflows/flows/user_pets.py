import json
import logging
import random
import os
import re
import sentry_sdk

import common.constants as common_constants
import common.dialogflow_framework.stdm.dialogflow_extention as dialogflow_extention
import common.dialogflow_framework.utils.state as state_utils
from common.utils import is_no, is_yes
import dialogflows.scopes as scopes
from dialogflows.flows.user_pets_states import State as UserPetsState
from dialogflows.flows.animals_states import State as AnimalsState
from common.animals import PETS_TEMPLATE, COLORS_TEMPLATE, CATS_DOGS_PHRASES

sentry_sdk.init(os.getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

breeds = json.load(open("breeds.json", 'r'))

CONF_1 = 1.0
CONF_2 = 0.99
CONF_3 = 0.95


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
    shared_memory = state_utils.get_shared_memory(vars)
    annotations = state_utils.get_last_human_utterance(vars)["annotations"]
    ner = annotations.get("ner", [])
    for entities in ner:
        if entities:
            for entity in entities:
                if entity.get("type", "") == "PER":
                    name = entity["text"]
                    if not shared_memory.get("users_pet_name", ""):
                        state_utils.save_to_shared_memory(vars, users_pet_name=name)
    return name


def choose_pet_phrase(vars, found_users_pet):
    shared_memory = state_utils.get_shared_memory(vars)
    used_cats_dogs_phrases_num = shared_memory.get("used_cats_dogs_phrases", {})
    new_used_cats_dog_phrases_num = used_cats_dogs_phrases_num
    cand_phrases = CATS_DOGS_PHRASES[found_users_pet]
    if used_cats_dogs_phrases_num and found_users_pet in used_cats_dogs_phrases_num:
        used_phrases_num = used_cats_dogs_phrases_num[found_users_pet]
        if len(used_phrases_num) < len(cand_phrases):
            while True:
                cand_phrase_num = random.randint(0, len(cand_phrases) - 1)
                if cand_phrase_num not in used_phrases_num:
                    break
        else:
            cand_phrase_num = random.randint(0, len(cand_phrases) - 1)
        if cand_phrase_num not in used_phrases_num:
            new_used_cats_dog_phrases_num[found_users_pet].append(cand_phrase_num)
    else:
        cand_phrase_num = random.randint(0, len(cand_phrases) - 1)
        new_used_cats_dog_phrases_num[found_users_pet] = [cand_phrase_num]
    pet_phrase = cand_phrases[cand_phrase_num]
    state_utils.save_to_shared_memory(vars, used_cats_dogs_phrases=new_used_cats_dog_phrases_num)
    return pet_phrase


def what_pets_request(ngrams, vars):
    flag = False
    bot_uttr = state_utils.get_last_bot_utterance(vars)["text"]
    user_uttr = state_utils.get_last_human_utterance(vars)["text"]
    isyes = is_yes(state_utils.get_last_human_utterance(vars))
    user_has = re.findall("i (have|had)", user_uttr)
    mention_pet = re.findall(PETS_TEMPLATE, user_uttr)
    asked_about_pets = "do you have pets" in bot_uttr.lower()
    if asked_about_pets and (isyes or user_has) and not mention_pet:
        flag = True
    logger.info(f"what_pets_request={flag}")
    return flag


def ask_about_name_request(ngrams, vars):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)["text"]
    bot_uttr = state_utils.get_last_bot_utterance(vars)["text"]
    isno = is_no(state_utils.get_last_human_utterance(vars))
    user_has_not = (re.findall("do you have a (cat|dog)", bot_uttr, re.IGNORECASE) and isno) and not \
        re.findall(PETS_TEMPLATE, user_uttr)
    shared_memory = state_utils.get_shared_memory(vars)
    asked_name = shared_memory.get("asked_name", False)
    if not user_has_not and not asked_name and not re.findall(r"(name|call)", user_uttr):
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


def is_dog_cat_request(ngrams, vars):
    flag = False
    bot_uttr = state_utils.get_last_bot_utterance(vars)["text"]
    user_uttr = state_utils.get_last_human_utterance(vars)["text"]
    user_mention_pet = re.findall(r"\b(cat|dog)s?\b", user_uttr)
    user_has = re.findall(r"\b(have|had)\b", user_uttr)
    asked_like = "what animals do you like" in bot_uttr.lower()
    if asked_like and user_mention_pet and not user_has:
        flag = True
    logger.info(f"is_dog_cat_request={flag}")
    return flag


def ask_about_breed_request(ngrams, vars):
    flag = False
    bot_uttr = state_utils.get_last_bot_utterance(vars)["text"]
    user_uttr = state_utils.get_last_human_utterance(vars)["text"]
    shared_memory = state_utils.get_shared_memory(vars)
    found_pet = re.findall(PETS_TEMPLATE, user_uttr)
    users_pet = shared_memory.get("users_pet", "")
    asked_name = shared_memory.get("asked_name", False)
    asked_breed = shared_memory.get("asked_breed", False)
    found_breed = re.findall("|".join(breeds.keys()), user_uttr)
    isno = is_no(state_utils.get_last_human_utterance(vars))
    user_has_not = (re.findall("do you have a (cat|dog)", bot_uttr, re.IGNORECASE) and isno) and not \
        re.findall(PETS_TEMPLATE, user_uttr)
    logger.info(f"ask_about_breed_request_isno {isno}")
    if not user_has_not and not asked_breed and (found_pet or asked_name or users_pet) and not found_breed:
        flag = True
    logger.info(f"ask_about_breed_request={flag}")
    return flag


def ask_about_color_request(ngrams, vars):
    flag = False
    bot_uttr = state_utils.get_last_bot_utterance(vars)["text"]
    user_uttr = state_utils.get_last_human_utterance(vars)["text"]
    shared_memory = state_utils.get_shared_memory(vars)
    found_pet = re.findall(PETS_TEMPLATE, user_uttr)
    users_pet = shared_memory.get("users_pet", "")
    asked_name = shared_memory.get("asked_name", False)
    asked_color = shared_memory.get("asked_color", False)
    found_color = re.findall(COLORS_TEMPLATE, user_uttr)
    isno = is_no(state_utils.get_last_human_utterance(vars))
    user_has_not = (re.findall("do you have a (cat|dog)", bot_uttr, re.IGNORECASE) and isno) and not \
        re.findall(PETS_TEMPLATE, user_uttr)
    logger.info(f"ask_about_color_request_isno {isno}")
    if not user_has_not and not asked_color and (found_pet or asked_name or users_pet) and not found_color:
        flag = True
    logger.info(f"ask_about_color_request={flag}")
    return flag


def ask_about_feeding_request(ngrams, vars):
    flag = False
    bot_uttr = state_utils.get_last_bot_utterance(vars)["text"]
    user_uttr = state_utils.get_last_human_utterance(vars)["text"]
    shared_memory = state_utils.get_shared_memory(vars)
    found_pet = re.findall(PETS_TEMPLATE, user_uttr)
    users_pet = shared_memory.get("users_pet", "")
    asked_feeding = shared_memory.get("asked_feeding", False)
    isno = is_no(state_utils.get_last_human_utterance(vars))
    user_has_not = (re.findall("do you have a (cat|dog)", bot_uttr, re.IGNORECASE) and isno) and not \
        re.findall(PETS_TEMPLATE, user_uttr)
    if not user_has_not and not asked_feeding and (found_pet or users_pet) and "feed" not in user_uttr:
        flag = True
    logger.info(f"ask_about_feeding_request={flag}")
    return flag


def tell_fact_about_breed_request(ngrams, vars):
    flag = False
    shared_memory = state_utils.get_shared_memory(vars)
    fact_about_breed = shared_memory.get("fact_about_breed", False)
    if not fact_about_breed:
        flag = True
    logger.info(f"tell_fact_about_breed_request={flag}")
    return flag


def to_animals_flow_request(ngrams, vars):
    flag = True
    logger.info(f"to_animals_flow_request={flag}")
    return flag


def what_pets_response(vars):
    response = "What pets do you have?"
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    return response


def ask_about_dog_cat_response(vars):
    found_users_pet = retrieve_and_save(vars)
    if found_users_pet:
        pet_phrase = choose_pet_phrase(vars, found_users_pet)
        response = f"{pet_phrase} Do you have a {found_users_pet}?"
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    return response


def ask_about_name_response(vars):
    found_users_pet = retrieve_and_save(vars)
    if found_users_pet:
        pet_phrase = choose_pet_phrase(vars, found_users_pet)
        response = f"{pet_phrase} What is your {found_users_pet}'s name?"
    else:
        response = "What is his name?"
    state_utils.save_to_shared_memory(vars, asked_name=True)
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    return response


def suggest_pet_response(vars):
    phrases = [phrase for pet_phrases in CATS_DOGS_PHRASES.values() for phrase in pet_phrases]
    response = random.choice(phrases)
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    return response


def ask_about_breed_response(vars):
    found_users_pet = retrieve_and_save(vars)
    found_users_pet_name = retrieve_and_save_name(vars)
    if found_users_pet:
        pet_phrase = choose_pet_phrase(vars, found_users_pet)
        if found_users_pet_name:
            response = f"{pet_phrase} What breed is {found_users_pet_name}?"
        else:
            response = f"{pet_phrase} What breed is your {found_users_pet}?"
    else:
        response = "What breed is it?"
    state_utils.save_to_shared_memory(vars, asked_breed=True)
    state_utils.set_confidence(vars, confidence=CONF_2)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    return response


def ask_about_color_response(vars):
    found_users_pet = retrieve_and_save(vars)
    found_users_pet_name = retrieve_and_save_name(vars)
    if found_users_pet:
        pet_phrase = choose_pet_phrase(vars, found_users_pet)
        if found_users_pet_name:
            response = f"{pet_phrase} What color is {found_users_pet_name}?"
        else:
            response = f"{pet_phrase} What color is your {found_users_pet}?"
    else:
        response = "What color is it?"
    state_utils.save_to_shared_memory(vars, asked_color=True)
    state_utils.set_confidence(vars, confidence=CONF_2)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    return response


def ask_about_feeding_response(vars):
    found_users_pet = retrieve_and_save(vars)
    found_users_pet_name = retrieve_and_save_name(vars)
    if found_users_pet:
        pet_phrase = choose_pet_phrase(vars, found_users_pet)
        if found_users_pet_name:
            response = f"{pet_phrase} How do you feed {found_users_pet_name}?"
        else:
            response = f"{pet_phrase} How do you feed your {found_users_pet}?"
    else:
        response = "How do you feed him?"
    state_utils.save_to_shared_memory(vars, asked_feeding=True)
    state_utils.set_confidence(vars, confidence=CONF_3)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    return response


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
    state_utils.save_to_shared_memory(vars, fact_about_breed=True)
    state_utils.set_confidence(vars, confidence=CONF_3)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    return response


def error_response(vars):
    state_utils.set_confidence(vars, 0)
    return ""


simplified_dialog_flow = dialogflow_extention.DFEasyFilling(UserPetsState.USR_START)

simplified_dialog_flow.add_user_serial_transitions(
    UserPetsState.USR_START,
    {
        UserPetsState.SYS_WHAT_PETS: what_pets_request,
        UserPetsState.SYS_IS_DOG_CAT: is_dog_cat_request,
        UserPetsState.SYS_NOT_HAVE: not_have_pets_request,
        UserPetsState.SYS_ASK_ABOUT_NAME: ask_about_name_request,
        UserPetsState.SYS_WHAT_BREED: ask_about_breed_request,
        UserPetsState.SYS_WHAT_COLOR: ask_about_color_request,
        (scopes.ANIMALS, AnimalsState.USR_START): to_animals_flow_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    UserPetsState.USR_WHAT_PETS,
    {
        UserPetsState.SYS_ASK_ABOUT_NAME: ask_about_name_request,
        UserPetsState.SYS_WHAT_BREED: ask_about_breed_request,
        UserPetsState.SYS_WHAT_COLOR: ask_about_color_request,
        (scopes.ANIMALS, AnimalsState.USR_START): to_animals_flow_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    UserPetsState.USR_ASK_ABOUT_DOG_CAT,
    {
        UserPetsState.SYS_ASK_ABOUT_NAME: ask_about_name_request,
        UserPetsState.SYS_WHAT_BREED: ask_about_breed_request,
        UserPetsState.SYS_WHAT_COLOR: ask_about_color_request,
        UserPetsState.SYS_ASK_ABOUT_FEEDING: ask_about_feeding_request,
        (scopes.ANIMALS, AnimalsState.USR_START): to_animals_flow_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    UserPetsState.USR_ASK_ABOUT_NAME,
    {
        UserPetsState.SYS_WHAT_BREED: ask_about_breed_request,
        UserPetsState.SYS_WHAT_COLOR: ask_about_color_request,
        UserPetsState.SYS_ASK_ABOUT_FEEDING: ask_about_feeding_request,
        (scopes.ANIMALS, AnimalsState.USR_START): to_animals_flow_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    UserPetsState.USR_NOT_HAVE,
    {
        (scopes.ANIMALS, AnimalsState.USR_START): to_animals_flow_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    UserPetsState.USR_WHAT_BREED,
    {
        UserPetsState.SYS_ASK_ABOUT_NAME: ask_about_name_request,
        UserPetsState.SYS_WHAT_COLOR: ask_about_color_request,
        UserPetsState.SYS_ASK_ABOUT_FEEDING: ask_about_feeding_request,
        UserPetsState.SYS_TELL_FACT_ABOUT_BREED: tell_fact_about_breed_request,
        (scopes.ANIMALS, AnimalsState.USR_START): to_animals_flow_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    UserPetsState.USR_WHAT_COLOR,
    {
        UserPetsState.SYS_ASK_ABOUT_NAME: ask_about_name_request,
        UserPetsState.SYS_WHAT_BREED: ask_about_breed_request,
        UserPetsState.SYS_ASK_ABOUT_FEEDING: ask_about_feeding_request,
        (scopes.ANIMALS, AnimalsState.USR_START): to_animals_flow_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    UserPetsState.USR_ASK_ABOUT_FEEDING,
    {
        UserPetsState.SYS_WHAT_BREED: ask_about_breed_request,
        UserPetsState.SYS_WHAT_COLOR: ask_about_color_request,
        (scopes.ANIMALS, AnimalsState.USR_START): to_animals_flow_request,
    },
)

simplified_dialog_flow.add_system_transition(UserPetsState.SYS_WHAT_PETS, UserPetsState.USR_WHAT_PETS,
                                             what_pets_response, )
simplified_dialog_flow.add_system_transition(UserPetsState.SYS_IS_DOG_CAT, UserPetsState.USR_ASK_ABOUT_DOG_CAT,
                                             ask_about_dog_cat_response, )
simplified_dialog_flow.add_system_transition(UserPetsState.SYS_NOT_HAVE, UserPetsState.USR_NOT_HAVE,
                                             suggest_pet_response, )
simplified_dialog_flow.add_system_transition(UserPetsState.SYS_ASK_ABOUT_NAME, UserPetsState.USR_ASK_ABOUT_NAME,
                                             ask_about_name_response, )
simplified_dialog_flow.add_system_transition(UserPetsState.SYS_WHAT_BREED, UserPetsState.USR_WHAT_BREED,
                                             ask_about_breed_response, )
simplified_dialog_flow.add_system_transition(UserPetsState.SYS_WHAT_COLOR, UserPetsState.USR_WHAT_COLOR,
                                             ask_about_color_response, )
simplified_dialog_flow.add_system_transition(UserPetsState.SYS_ASK_ABOUT_FEEDING, UserPetsState.USR_ASK_ABOUT_FEEDING,
                                             ask_about_feeding_response, )
simplified_dialog_flow.add_system_transition(UserPetsState.SYS_TELL_FACT_ABOUT_BREED,
                                             UserPetsState.USR_TELL_FACT_ABOUT_BREED, tell_fact_about_breed_response, )

simplified_dialog_flow.set_error_successor(UserPetsState.USR_START, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.SYS_WHAT_PETS, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.SYS_IS_DOG_CAT, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.USR_WHAT_PETS, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.SYS_ASK_ABOUT_NAME, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.USR_ASK_ABOUT_NAME, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.SYS_NOT_HAVE, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.USR_NOT_HAVE, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.SYS_WHAT_BREED, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.SYS_WHAT_COLOR, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.USR_WHAT_BREED, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.USR_WHAT_COLOR, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.SYS_ASK_ABOUT_FEEDING, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.USR_ASK_ABOUT_FEEDING, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.SYS_TELL_FACT_ABOUT_BREED, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.USR_TELL_FACT_ABOUT_BREED, UserPetsState.SYS_ERR)

simplified_dialog_flow.add_system_transition(
    UserPetsState.SYS_ERR,
    (scopes.MAIN, scopes.State.USR_ROOT),
    error_response,
)

dialogflow = simplified_dialog_flow.get_dialogflow()
