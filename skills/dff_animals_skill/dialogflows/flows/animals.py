import json
import logging
import random
import os
import re
import en_core_web_sm
import inflect
import sentry_sdk

import common.constants as common_constants
import common.dialogflow_framework.stdm.dialogflow_extention as dialogflow_extention
import common.dialogflow_framework.utils.state as state_utils
from common.universal_templates import if_chat_about_particular_topic
from common.utils import is_yes, is_no
from common.animals import PETS_TEMPLATE, ANIMALS_FIND_TEMPLATE, LIKE_ANIMALS_REQUESTS, WILD_ANIMALS, \
    WHAT_PETS_I_HAVE, HAVE_LIKE_PETS_TEMPLATE, HAVE_PETS_TEMPLATE, LIKE_PETS_TEMPLATE, TRIGGER_PHRASES

import dialogflows.scopes as scopes
from dialogflows.flows.my_pets_states import State as MyPetsState
from dialogflows.flows.user_pets_states import State as UserPetsState
from dialogflows.flows.wild_animals_states import State as WildAnimalsState
from dialogflows.flows.animals_states import State as AS

sentry_sdk.init(os.getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

nlp = en_core_web_sm.load()
p = inflect.engine()

breeds = json.load(open("breeds.json", 'r'))

CONF_1 = 1.0
CONF_2 = 0.98
CONF_3 = 0.95
CONF_4 = 0.9


def lets_talk_about_request(vars):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    have_pets = re.search(HAVE_LIKE_PETS_TEMPLATE, user_uttr["text"])
    found_prompt = any([phrase in bot_uttr for phrase in TRIGGER_PHRASES])
    isyes = is_yes(user_uttr)
    chat_about = if_chat_about_particular_topic(user_uttr, bot_uttr, compiled_pattern=ANIMALS_FIND_TEMPLATE)
    if have_pets or chat_about or (found_prompt and isyes):
        flag = True
    logger.info(f"lets_talk_about_request={flag}")
    return flag


def have_pets_request(ngrams, vars):
    flag = False
    text = state_utils.get_last_human_utterance(vars)["text"]
    if re.search(HAVE_PETS_TEMPLATE, text):
        flag = True
    logger.info(f"have_pets_request={flag}")
    return flag


def like_animals_request(ngrams, vars):
    flag = False
    text = state_utils.get_last_human_utterance(vars)["text"]
    shared_memory = state_utils.get_shared_memory(vars)
    started = shared_memory.get("start", False)
    my_pet = shared_memory.get("my_pet", "")
    told_about_cat = shared_memory.get("told_about_cat", False)
    told_about_dog = shared_memory.get("told_about_dog", False)
    told_about = False
    if my_pet == "cat":
        told_about = told_about_cat
    if my_pet == "dog":
        told_about = told_about_dog
    if re.search(LIKE_PETS_TEMPLATE, text) or (not told_about and started):
        flag = True
    logger.info(f"like_animals_request={flag}")
    return flag


def user_likes_animal_request(ngrams, vars):
    flag = False
    text = state_utils.get_last_human_utterance(vars)["text"]
    animal = re.findall("i like (.*?)", text)
    if animal and len(animal[0].split()) <= 3:
        flag = True
    logger.info(f"user_likes_request={flag}")
    return flag


def mention_pets_request(ngrams, vars):
    flag = False
    text = state_utils.get_last_human_utterance(vars)["text"]
    shared_memory = state_utils.get_shared_memory(vars)
    started = shared_memory.get("start", False)
    if re.search(PETS_TEMPLATE, text) and not started:
        flag = True
    logger.info(f"mention_pets_request={flag}")
    return flag


def mention_animals_request(ngrams, vars):
    flag = False
    shared_memory = state_utils.get_shared_memory(vars)
    started = shared_memory.get("start", False)
    annotations = state_utils.get_last_human_utterance(vars)["annotations"]
    conceptnet = annotations.get("conceptnet", {})
    for elem, triplets in conceptnet.items():
        if "SymbolOf" in triplets:
            objects = triplets["SymbolOf"]
            if "animal" in objects and not started:
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
    user_asks_about_pets = re.search(HAVE_PETS_TEMPLATE, text)
    found_pet_word = re.findall(r"(pet|pets)", text)
    found_pet = re.findall(PETS_TEMPLATE, text)
    check_linkto = lets_talk_about_request(vars) or (linkto_like_animals and user_agrees) or text == "animals"
    if not user_asks_about_pets and not found_pet_word and not found_pet and \
            not shared_memory.get("what_animals", False) and check_linkto:
        flag = True
    logger.info(f"sys_what_animals_request={flag}")
    return flag


def sys_have_pets_request(ngrams, vars):
    flag = False
    text = state_utils.get_last_human_utterance(vars)["text"]
    shared_memory = state_utils.get_shared_memory(vars)
    found_users_pet = shared_memory.get("users_pet", "")
    started = shared_memory.get("start", False)
    pet = re.search(PETS_TEMPLATE, text)
    if not shared_memory.get("have_pets", False) and not found_users_pet and \
            ((lets_talk_about_request(vars) and not pet) or started):
        flag = True
    logger.info(f"sys_have_pets_request={flag}")
    return flag


def is_wild_request(ngrams, vars):
    flag = False
    text = state_utils.get_last_human_utterance(vars)["text"]
    shared_memory = state_utils.get_shared_memory(vars)
    used_is_wild = shared_memory.get("is_wild", False)
    if not re.search(PETS_TEMPLATE, text) and not used_is_wild:
        flag = True
    logger.info(f"is_wild_request={flag}")
    return flag


def is_not_wild_request(ngrams, vars):
    flag = False
    text = state_utils.get_last_human_utterance(vars)["text"]
    if re.search(PETS_TEMPLATE, text):
        flag = True
    logger.info(f"is_not_wild_request={flag}")
    return flag


def my_pets_request(ngrams, vars):
    flag = False
    bot_uttr = state_utils.get_last_bot_utterance(vars)["text"]
    isyes = is_yes(state_utils.get_last_human_utterance(vars))
    shared_memory = state_utils.get_shared_memory(vars)
    told_about_cat = shared_memory.get("told_about_cat", False)
    told_about_dog = shared_memory.get("told_about_dog", False)
    if "Would you like to learn more about my pets?" in bot_uttr and isyes and not (told_about_cat and told_about_dog):
        flag = True
    logger.info(f"my_pets_request={flag}")
    return flag


def user_has_pets_request(ngrams, vars):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)["text"]
    bot_uttr = state_utils.get_last_bot_utterance(vars)["text"]
    isno = is_no(state_utils.get_last_human_utterance(vars))
    isyes = is_yes(state_utils.get_last_human_utterance(vars))
    user_has = re.findall("i (have|had)", user_uttr)
    bot_asked_like = "do you like animals" in bot_uttr
    if (re.search(PETS_TEMPLATE, user_uttr) and not isno) or (re.search(PETS_TEMPLATE, bot_uttr)
                                                              and (isyes or user_has)) or (bot_asked_like and user_has):
        flag = True
    logger.info(f"user_has_pets_request={flag}")
    return flag


def user_has_not_pets_request(ngrams, vars):
    flag = False
    isno = is_no(state_utils.get_last_human_utterance(vars))
    text = state_utils.get_last_human_utterance(vars)["text"]
    if not re.search(PETS_TEMPLATE, text) or isno:
        flag = True
    logger.info(f"user_has_not_pets_request={flag}")
    return flag


def user_likes_request(ngrams, vars):
    flag = False
    isno = is_no(state_utils.get_last_human_utterance(vars))
    if not isno:
        flag = True
    logger.info(f"user_likes_request={flag}")
    return flag


def user_not_likes_request(ngrams, vars):
    flag = False
    isno = is_no(state_utils.get_last_human_utterance(vars))
    if isno:
        flag = True
    logger.info(f"user_not_likes_request={flag}")
    return flag


def no_animals_mentioned_request(ngrams, vars):
    flag = True
    logger.info(f"no_animals_mentioned_request={flag}")
    return flag


def has_pet_request(ngrams, vars):
    flag = False
    if not is_no(state_utils.get_last_human_utterance(vars)):
        flag = True
    logger.info(f"has_pet_request={flag}")
    return flag


def what_wild_request(ngrams, vars):
    flag = True
    text = state_utils.get_last_human_utterance(vars)["text"]
    shared_memory = state_utils.get_shared_memory(vars)
    user_asks_about_pets = re.search(PETS_TEMPLATE, text)
    is_wild = shared_memory.get("is_wild", False)
    what_wild = shared_memory.get("what_wild", False)
    logger.info(f"what_wild_request, is wild {is_wild}, what wild {what_wild}")
    started = shared_memory.get("start", False)
    if is_wild or what_wild or user_asks_about_pets or (not lets_talk_about_request(vars) and not started):
        flag = False
    logger.info(f"what_wild_request={flag}")
    return flag


def wants_more_request(ngrams, vars):
    flag = False
    isno = is_no(state_utils.get_last_human_utterance(vars))
    if not isno:
        flag = True
    logger.info(f"wants_more_request={flag}")
    return flag


def not_wants_more_request(ngrams, vars):
    flag = False
    isno = is_no(state_utils.get_last_human_utterance(vars))
    if isno:
        flag = True
    logger.info(f"not_wants_more_request={flag}")
    return flag


def what_animals_response(vars):
    what_i_like = random.choice(WILD_ANIMALS)
    response = f"{what_i_like} What animals do you like?"
    state_utils.save_to_shared_memory(vars, start=True)
    state_utils.save_to_shared_memory(vars, what_animals=True)
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    return response


def have_pets_response(vars):
    my_pet_info = random.choice(WHAT_PETS_I_HAVE)
    my_pet = my_pet_info["pet"]
    my_pet_name = my_pet_info["name"]
    my_pet_breed = my_pet_info["breed"]
    sentence = my_pet_info["sentence"]
    state_utils.save_to_shared_memory(vars, start=True)
    state_utils.save_to_shared_memory(vars, my_pet=my_pet)
    state_utils.save_to_shared_memory(vars, my_pet_name=my_pet_name)
    state_utils.save_to_shared_memory(vars, my_pet_breed=my_pet_breed)
    response = f"{sentence} Do you have pets?"
    state_utils.save_to_shared_memory(vars, start=True)
    state_utils.save_to_shared_memory(vars, have_pets=True)
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    return response


def tell_about_pets_response(vars):
    my_pet_info = random.choice(WHAT_PETS_I_HAVE)
    my_pet = my_pet_info["pet"]
    my_pet_name = my_pet_info["name"]
    my_pet_breed = my_pet_info["breed"]
    sentence = my_pet_info["sentence"]
    state_utils.save_to_shared_memory(vars, start=True)
    state_utils.save_to_shared_memory(vars, my_pet=my_pet)
    state_utils.save_to_shared_memory(vars, my_pet_name=my_pet_name)
    state_utils.save_to_shared_memory(vars, my_pet_breed=my_pet_breed)
    response = f"{sentence} Would you like to learn more about my {my_pet}?"
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    return response


def mention_pets_response(vars):
    replace_plural = {"cats": "cat", "dogs": "dog", "rats": "rat"}
    text = state_utils.get_last_human_utterance(vars)["text"]
    pet = re.findall(PETS_TEMPLATE, text)
    if pet[0] in replace_plural:
        found_pet = replace_plural[pet[0]]
    else:
        found_pet = pet[0]
    response = f"Do you have a {found_pet}?"
    state_utils.save_to_shared_memory(vars, start=True)
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    return response


def mention_animals_response(vars):
    annotations = state_utils.get_last_human_utterance(vars)["annotations"]
    animal = ""
    conceptnet = annotations.get("conceptnet", {})
    for elem, triplets in conceptnet.items():
        if "SymbolOf" in triplets:
            objects = triplets["SymbolOf"]
            if "animal" in objects:
                animal = elem
    response = f"Awesome! Do you like {animal}?"
    state_utils.save_to_shared_memory(vars, start=True)
    state_utils.set_confidence(vars, confidence=CONF_4)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    return response


def what_wild_response(vars):
    what_i_like = random.choice(WILD_ANIMALS)
    response = f"{what_i_like} What wild animals do you like?"
    state_utils.save_to_shared_memory(vars, start=True)
    state_utils.save_to_shared_memory(vars, what_wild=True)
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    return response


def error_response(vars):
    state_utils.save_to_shared_memory(vars, start=False)
    state_utils.set_confidence(vars, 0)
    return ""


simplified_dialog_flow = dialogflow_extention.DFEasyFilling(AS.USR_START)

simplified_dialog_flow.add_user_serial_transitions(
    AS.USR_START,
    {
        AS.SYS_WHAT_ANIMALS: sys_what_animals_request,
        AS.SYS_Q_HAVE_PETS: sys_have_pets_request,
        (scopes.WILD_ANIMALS, WildAnimalsState.SYS_WHY_DO_YOU_LIKE): user_likes_animal_request,
        AS.SYS_WHAT_WILD_ANIMALS: what_wild_request,
        AS.SYS_HAVE_PETS: have_pets_request,
        AS.SYS_LIKE_ANIMALS: like_animals_request,
        AS.SYS_MENTION_PETS: mention_pets_request,
        AS.SYS_MENTION_ANIMALS: mention_animals_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    AS.USR_WHAT_ANIMALS,
    {
        (scopes.WILD_ANIMALS, WildAnimalsState.USR_START): is_wild_request,
        (scopes.USER_PETS, UserPetsState.USR_START): is_not_wild_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    AS.USR_HAVE_PETS,
    {
        (scopes.USER_PETS, UserPetsState.USR_START): user_has_pets_request,
        (scopes.ANIMALS, AS.USR_START): user_has_not_pets_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    AS.USR_WHAT_WILD_ANIMALS,
    {
        (scopes.WILD_ANIMALS, WildAnimalsState.USR_START): is_wild_request,
        (scopes.USER_PETS, UserPetsState.USR_START): is_not_wild_request,
        (scopes.ANIMALS, AS.USR_START): no_animals_mentioned_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    AS.USR_MENTION_PETS,
    {
        (scopes.USER_PETS, UserPetsState.USR_START): user_has_pets_request,
        (scopes.ANIMALS, AS.USR_START): user_has_not_pets_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    AS.USR_MENTION_ANIMALS,
    {
        (scopes.WILD_ANIMALS, WildAnimalsState.USR_START): user_likes_request,
        (scopes.ANIMALS, AS.USR_START): user_not_likes_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    AS.USR_TELL_ABOUT_PETS,
    {
        (scopes.MY_PETS, MyPetsState.USR_START): wants_more_request,
        (scopes.ANIMALS, AS.USR_START): not_wants_more_request,
    },
)

simplified_dialog_flow.add_system_transition(AS.SYS_WHAT_ANIMALS, AS.USR_WHAT_ANIMALS, what_animals_response, )
simplified_dialog_flow.add_system_transition(AS.SYS_Q_HAVE_PETS, AS.USR_HAVE_PETS, have_pets_response, )
simplified_dialog_flow.add_system_transition(AS.SYS_HAVE_PETS, AS.USR_TELL_ABOUT_PETS, tell_about_pets_response, )
simplified_dialog_flow.add_system_transition(AS.SYS_WHAT_WILD_ANIMALS, AS.USR_WHAT_WILD_ANIMALS, what_wild_response, )
simplified_dialog_flow.add_system_transition(AS.SYS_MENTION_PETS, AS.USR_MENTION_PETS, mention_pets_response, )
simplified_dialog_flow.add_system_transition(AS.SYS_MENTION_ANIMALS, AS.USR_MENTION_ANIMALS, mention_animals_response, )
simplified_dialog_flow.add_system_transition(AS.SYS_LIKE_ANIMALS, AS.USR_TELL_ABOUT_PETS, tell_about_pets_response, )
simplified_dialog_flow.add_system_transition(AS.SYS_ERR, (scopes.MAIN, scopes.State.USR_ROOT), error_response, )

simplified_dialog_flow.set_error_successor(AS.USR_START, AS.SYS_ERR)
simplified_dialog_flow.set_error_successor(AS.SYS_WHAT_ANIMALS, AS.SYS_ERR)
simplified_dialog_flow.set_error_successor(AS.USR_WHAT_ANIMALS, AS.SYS_ERR)
simplified_dialog_flow.set_error_successor(AS.SYS_Q_HAVE_PETS, AS.SYS_ERR)
simplified_dialog_flow.set_error_successor(AS.USR_HAVE_PETS, AS.SYS_ERR)
simplified_dialog_flow.set_error_successor(AS.USR_TELL_ABOUT_PETS, AS.SYS_ERR)
simplified_dialog_flow.set_error_successor(AS.SYS_WHAT_WILD_ANIMALS, AS.SYS_ERR)
simplified_dialog_flow.set_error_successor(AS.USR_WHAT_WILD_ANIMALS, AS.SYS_ERR)
simplified_dialog_flow.set_error_successor(AS.SYS_MENTION_PETS, AS.SYS_ERR)
simplified_dialog_flow.set_error_successor(AS.USR_MENTION_PETS, AS.SYS_ERR)
simplified_dialog_flow.set_error_successor(AS.SYS_MENTION_ANIMALS, AS.SYS_ERR)
simplified_dialog_flow.set_error_successor(AS.USR_MENTION_ANIMALS, AS.SYS_ERR)
simplified_dialog_flow.set_error_successor(AS.SYS_LIKE_ANIMALS, AS.SYS_ERR)
simplified_dialog_flow.set_error_successor(AS.USR_TELL_ABOUT_PETS, AS.SYS_ERR)

dialogflow = simplified_dialog_flow.get_dialogflow()
