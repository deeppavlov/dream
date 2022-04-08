import logging
import random
import os
import re
import sentry_sdk

import common.constants as common_constants
from dff import dialogflow_extension
import common.dialogflow_framework.utils.state as state_utils
import common.dialogflow_framework.utils.condition as condition_utils
from common.utils import is_no
from common.animals import (
    MY_PET_FACTS,
    pet_games,
    stop_about_animals,
    fallbacks,
    DO_YOU_HAVE_TEMPLATE,
    ANIMALS_FIND_TEMPLATE,
)
from common.universal_templates import NOT_LIKE_PATTERN, if_lets_chat
import dialogflows.scopes as scopes
from dialogflows.flows.my_pets_states import State as MyPetsState
from dialogflows.flows.animals_states import State as AnimalsState
from dialogflows.flows.animals import make_my_pets_info

sentry_sdk.init(os.getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)

CONF_1 = 1.0
CONF_2 = 0.99
CONF_3 = 0.95
CONF_4 = 0.0


def answer_users_question(vars):
    make_my_pets_info(vars)
    user_uttr = state_utils.get_last_human_utterance(vars)
    user_text = user_uttr["text"]
    shared_memory = state_utils.get_shared_memory(vars)
    my_pet = shared_memory.get("my_pet", "")
    my_pets_info = shared_memory.get("my_pets_info", {})
    my_pet_name = my_pets_info[my_pet]["name"]
    my_pet_breed = my_pets_info[my_pet]["breed"]
    mention_pet = re.findall(r"(cat|dog)", user_text)
    if mention_pet and mention_pet[0] != my_pet:
        my_pet = mention_pet[0]
        my_pet_name = my_pets_info[my_pet]["name"]
        my_pet_breed = my_pets_info[my_pet]["breed"]

    answer = ""
    conf = CONF_2
    continue_flag = common_constants.CAN_CONTINUE_SCENARIO
    logger.info(f"answer_users_question {user_text} {my_pet_name}")
    if "?" in user_text and ("your" in user_text or (my_pet_name and my_pet_name in user_text)):
        if "name" in user_text and my_pet and my_pet_name:
            answer = f"My {my_pet}'s name is {my_pet_name}."
        elif "breed" in user_text and my_pet and my_pet_breed:
            answer = f"My {my_pet}'s breed is {my_pet_breed}."
        elif "play" in user_text:
            if my_pet:
                games = " and ".join(pet_games[my_pet])
                answer = f"I like to play with my {my_pet} different games, such as {games}."
            else:
                answer = "I like to play with my pet different games, such as run and fetch."
        elif "walk" in user_text and my_pet:
            answer = f"I walk with my {my_pet} every morning."
        elif "like" in user_text or "love" in user_text and my_pet:
            answer = f"Yes, I love my {my_pet}."
        elif re.findall(r"you (like|love) dogs or cats", user_text):
            answer = "I like dogs and cats."
        elif "tricks" in user_text and my_pet:
            answer = f"Yes, my {my_pet} knows many tricks, for example high five."
        elif "meow" in user_text:
            answer = "My cat does not meow very often."
        elif "bark" in user_text:
            answer = "My dog can bark very loudly."
        elif any([kwrd in user_text for kwrd in ["meet", "see", "watch"]]):
            answer = "I would like to show you my dog if I had a screen."
    used_fallbacks = shared_memory.get("used_fallbacks", [])
    if "?" in user_text:
        if any([elem in user_text for elem in ["do you like swimming", "you like to swim", "you swim"]]):
            answer = "Yes, I like swimming."
        elif re.findall(r"you have (a )?(robot|vacuum|cleaner)", user_text) or re.findall(
            r"about (your )?(robot|vacuum|cleaner)", user_text
        ):
            answer = "I have a Xiaomi robot vacuum cleaner."
        elif re.findall(r"you have (a )?(tablet|pc)", user_text) or re.findall(r"about (your )?(tablet|pc)", user_text):
            answer = "I have a Samsung tablet PC."
        else:
            conf = CONF_2
            continue_flag = common_constants.CAN_CONTINUE_SCENARIO
            found_num = -1
            found_fallback = ""
            for f_num, fallback in enumerate(fallbacks):
                if f_num not in used_fallbacks:
                    found_fallback = fallback
                    found_num = f_num
                    break
            if found_fallback:
                answer = found_fallback
                used_fallbacks.append(found_num)
                state_utils.save_to_shared_memory(vars, used_fallbacks=used_fallbacks)
    return answer, my_pet, conf, continue_flag


def stop_animals_request(ngrams, vars):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    shared_memory = state_utils.get_shared_memory(vars)
    if stop_about_animals(user_uttr, shared_memory):
        flag = True
    logger.info(f"stop_animals_request={flag}")
    return flag


def if_about_users_pet(ngrams, vars):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    if re.findall(
        r"(tell|talk|hear)(.*)(my )(cat|dog|kitten|kitty|puppy|rat|bird|fish|hamster|parrot)", user_uttr["text"]
    ):
        flag = True
    logger.info(f"about_users_pet_request={flag}")
    return flag


def about_pet_request(ngrams, vars):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    isno = is_no(state_utils.get_last_human_utterance(vars))
    dontlike = re.findall(r"(do not like |don't like |hate )(cat|dog)", user_uttr["text"])
    shared_memory = state_utils.get_shared_memory(vars)
    told_about_cat = shared_memory.get("told_about_cat", False)
    have_cat = re.findall(r"(do|did) you have (a )?(cat|kitty|kitten)s?", user_uttr["text"])
    told_about_dog = shared_memory.get("told_about_dog", False)
    have_dog = re.findall(r"(do|did) you have (a )?(dog|puppy)s?", user_uttr["text"])
    about_users_pet = if_about_users_pet(ngrams, vars)
    if (
        not about_users_pet
        and not dontlike
        and (not isno or have_cat)
        and (not told_about_cat or have_cat or not told_about_dog or have_dog)
    ):
        flag = True
    my_pet = shared_memory.get("my_pet", "")
    bot_asked_pet = re.findall(DO_YOU_HAVE_TEMPLATE, bot_uttr["text"])

    all_facts_used = False
    if my_pet:
        used_facts = shared_memory.get("used_facts", {}).get(my_pet, [])
        all_facts = MY_PET_FACTS[my_pet]
        if len(all_facts) == len(used_facts):
            all_facts_used = True
    prev_state = condition_utils.get_last_state(vars)
    prev_skill = bot_uttr.get("active_skill", "")
    if (
        my_pet
        and prev_skill == "dff_animals_skill"
        and str(prev_state).split(".")[-1] == "SYS_MY_PET"
        and all_facts_used
    ):
        if my_pet == "cat":
            my_pet = "dog"
        elif my_pet == "dog":
            my_pet = "cat"
        new_all_facts_used = False
        used_facts = shared_memory.get("used_facts", {}).get(my_pet, [])
        all_facts = MY_PET_FACTS[my_pet]
        if len(all_facts) == len(used_facts):
            new_all_facts_used = True
        if not new_all_facts_used:
            flag = True

    if my_pet:
        ans, pet, *_ = answer_users_question(vars)
        if ans and ((pet != "cat" and told_about_dog) or (pet != "dog" and told_about_cat)):
            flag = False
        used_facts = shared_memory.get("used_facts", {}).get(my_pet, [])
        if len(used_facts) > 0 and prev_skill != "dff_animals_skill":
            flag = False
    cat_intro = shared_memory.get("cat_intro", False)
    dog_intro = shared_memory.get("dog_intro", False)
    if (my_pet == "cat" and cat_intro) or (my_pet == "dog" and dog_intro):
        flag = False
    if ("do you have pets" in bot_uttr["text"].lower() or bot_asked_pet) and isno:
        flag = True
    if if_lets_chat(user_uttr["text"]) and not re.findall(ANIMALS_FIND_TEMPLATE, user_uttr["text"]):
        flag = False
    logger.info(f"about_pet_request={flag}")
    return flag


def my_pet_request(ngrams, vars):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    prev_active_skill = bot_uttr.get("active_skill", "")
    dontlike = re.findall(r"(do not like |don't like |hate )(cat|dog)", user_uttr["text"])
    isno = is_no(user_uttr)
    shared_memory = state_utils.get_shared_memory(vars)
    my_pet = shared_memory.get("my_pet", "")
    all_facts_used = False
    start_using_facts = False
    if my_pet:
        used_facts = shared_memory.get("used_facts", {}).get(my_pet, [])
        all_facts = MY_PET_FACTS[my_pet]
        if len(all_facts) == len(used_facts):
            all_facts_used = True
        if len(used_facts) > 0:
            start_using_facts = True
    about_users_pet = if_about_users_pet(ngrams, vars)
    if not about_users_pet and my_pet and not dontlike and not all_facts_used:
        flag = True
    if start_using_facts and prev_active_skill != "dff_animals_skill":
        flag = False
    if re.findall(r"(would you like|can tell you more)", bot_uttr["text"], re.IGNORECASE) and isno:
        flag = False
    logger.info(f"my_pet_request={flag}")
    return flag


def scenario_end_request(ngrams, vars):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    isno = is_no(user_uttr)
    dont_like = re.findall(NOT_LIKE_PATTERN, user_uttr["text"])
    if re.findall(r"can tell you more", user_uttr["text"]) and (isno or dont_like):
        flag = True
    logger.info(f"scenario_end_request={flag}")
    return flag


def scenario_end_response(vars):
    response = "I was very happy to tell you about my pets! You are a wonderful person!"
    state_utils.set_confidence(vars, confidence=CONF_2)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    return response


def user_asked_about_pet(user_uttr, my_pet):
    have_cat = re.findall(r"(do|did) you have (a )?(cat|kitty|kitten)s?", user_uttr["text"])
    if have_cat:
        my_pet = "cat"
    have_dog = re.findall(r"(do|did) you have (a )?(dog|puppy)s?", user_uttr["text"])
    if have_dog:
        my_pet = "dog"
    about_my_cat = re.findall(r"(tell|talk|hear|know)(.*)(your )(cat|kitty|kitten)s?", user_uttr["text"])
    if about_my_cat:
        my_pet = "cat"
    about_my_dog = re.findall(r"(tell|talk|hear|know)(.*)(your )(dog|puppy)s?", user_uttr["text"])
    if about_my_dog:
        my_pet = "dog"
    return my_pet


def tell_about_pet_response(vars):
    shared_memory = state_utils.get_shared_memory(vars)
    my_pet = shared_memory.get("my_pet", "")
    make_my_pets_info(vars)
    if not my_pet:
        my_pet = random.choice(["cat", "dog"])
        state_utils.save_to_shared_memory(vars, my_pet=my_pet)
    user_uttr = state_utils.get_last_human_utterance(vars)
    my_pet = user_asked_about_pet(user_uttr, my_pet)
    all_facts_used = False
    used_facts = shared_memory.get("used_facts", {}).get(my_pet, [])
    all_facts = MY_PET_FACTS[my_pet]
    if len(all_facts) == len(used_facts):
        all_facts_used = True
    if all_facts_used:
        if my_pet == "cat":
            my_pet = "dog"
        elif my_pet == "dog":
            my_pet = "cat"
    state_utils.save_to_shared_memory(vars, my_pet=my_pet)

    my_pets_info = shared_memory["my_pets_info"]
    sentence = my_pets_info[my_pet]["sentence"]
    name = my_pets_info[my_pet]["name"]
    breed = my_pets_info[my_pet]["breed"]
    if my_pet == "cat":
        state_utils.save_to_shared_memory(vars, cat_intro=True)
    if my_pet == "dog":
        state_utils.save_to_shared_memory(vars, dog_intro=True)
    answer, _, conf, continue_flag = answer_users_question(vars)
    if (name in answer and name in sentence) or (breed in answer and breed in sentence):
        response = f"{sentence} Would you like to learn more about my {my_pet}?".strip()
    else:
        response = f"{answer} {sentence} Would you like to learn more about my {my_pet}?".strip()
    state_utils.save_to_shared_memory(vars, start=True)
    state_utils.set_confidence(vars, confidence=conf)
    state_utils.set_can_continue(vars, continue_flag=continue_flag)
    return response


def find_fact(vars, fact_list, pet):
    shared_memory = state_utils.get_shared_memory(vars)
    used_facts = shared_memory.get("used_facts", {})
    used_pet_facts = used_facts.get(pet, [])
    fact_dict = {}
    for n, elem in enumerate(fact_list[pet]):
        fact_dict = elem
        if n not in used_pet_facts:
            used_pet_facts.append(n)
            used_facts[pet] = used_pet_facts
            state_utils.save_to_shared_memory(vars, used_facts=used_facts)
            break
    return fact_dict


def my_pet_response(vars):
    shared_memory = state_utils.get_shared_memory(vars)
    my_pet = shared_memory.get("my_pet", "")
    make_my_pets_info(vars)
    response = ""
    continue_flag = common_constants.CAN_CONTINUE_SCENARIO
    conf = CONF_2
    if my_pet:
        fact_dict = find_fact(vars, MY_PET_FACTS, my_pet)
        fact = fact_dict.get("statement", "")
        question = fact_dict.get("question", "")
        answer, _, conf, continue_flag = answer_users_question(vars)
        response = f"{answer} {fact} {question}".strip().replace("  ", " ")
    if my_pet == "cat":
        state_utils.save_to_shared_memory(vars, told_about_cat=True)
        state_utils.save_to_shared_memory(vars, cat=True)
        state_utils.save_to_shared_memory(vars, start_about_cat=False)
    if my_pet == "dog":
        state_utils.save_to_shared_memory(vars, told_about_dog=True)
        state_utils.save_to_shared_memory(vars, dog=True)
        state_utils.save_to_shared_memory(vars, start_about_dog=False)
    state_utils.save_to_shared_memory(vars, start=True)
    if response:
        state_utils.set_confidence(vars, confidence=conf)
        state_utils.set_can_continue(vars, continue_flag=continue_flag)
    else:
        state_utils.set_confidence(vars, confidence=CONF_4)
        state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_NOT_CONTINUE)
    logger.info(f"my_pet_response: {response}")
    return response


def to_animals_flow_request(ngrams, vars):
    flag = True
    logger.info(f"to_animals_flow_request={flag}")
    return flag


def error_response(vars):
    state_utils.set_confidence(vars, 0)
    return ""


simplified_dialog_flow = dialogflow_extension.DFEasyFilling(MyPetsState.USR_START)

simplified_dialog_flow.add_user_serial_transitions(
    MyPetsState.USR_START,
    {
        MyPetsState.SYS_ERR: stop_animals_request,
        MyPetsState.SYS_ABOUT_PET: about_pet_request,
        MyPetsState.SYS_MY_PET: my_pet_request,
        (scopes.ANIMALS, AnimalsState.USR_START): to_animals_flow_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    MyPetsState.USR_ABOUT_PET,
    {
        MyPetsState.SYS_ERR: stop_animals_request,
        MyPetsState.SYS_MY_PET: my_pet_request,
        (scopes.ANIMALS, AnimalsState.USR_START): to_animals_flow_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    MyPetsState.USR_MY_PET,
    {
        MyPetsState.SYS_END: scenario_end_request,
        MyPetsState.SYS_ERR: stop_animals_request,
        MyPetsState.SYS_MY_PET: my_pet_request,
        MyPetsState.SYS_ABOUT_PET: about_pet_request,
        (scopes.ANIMALS, AnimalsState.USR_START): to_animals_flow_request,
    },
)

simplified_dialog_flow.add_system_transition(
    MyPetsState.SYS_ABOUT_PET,
    MyPetsState.USR_ABOUT_PET,
    tell_about_pet_response,
)
simplified_dialog_flow.add_system_transition(
    MyPetsState.SYS_END,
    MyPetsState.USR_END,
    scenario_end_response,
)
simplified_dialog_flow.add_system_transition(
    MyPetsState.SYS_MY_PET,
    MyPetsState.USR_MY_PET,
    my_pet_response,
)
simplified_dialog_flow.add_system_transition(
    MyPetsState.SYS_ERR,
    (scopes.MAIN, scopes.State.USR_ROOT),
    error_response,
)

simplified_dialog_flow.set_error_successor(MyPetsState.USR_START, MyPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(MyPetsState.SYS_ABOUT_PET, MyPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(MyPetsState.SYS_MY_PET, MyPetsState.SYS_ERR)

dialogflow = simplified_dialog_flow.get_dialogflow()
