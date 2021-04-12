import logging
import random
import os
import re
import sentry_sdk

import common.constants as common_constants
import common.dialogflow_framework.stdm.dialogflow_extention as dialogflow_extention
import common.dialogflow_framework.utils.state as state_utils
from common.utils import is_no
from common.animals import MY_CAT, MY_DOG, WHAT_PETS_I_HAVE
import dialogflows.scopes as scopes
from dialogflows.flows.my_pets_states import State as MyPetsState
from dialogflows.flows.animals_states import State as AnimalsState

sentry_sdk.init(os.getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

questions_pets = ["Would you like to learn more about {}?", "More about {}?", "Do you want to hear more about {}?",
                  "Something else about {}?", "Should I continue?"]
random.shuffle(MY_CAT)
random.shuffle(MY_DOG)

CONF_1 = 1.0


def about_cat_request(ngrams, vars):
    flag = False
    text = state_utils.get_last_human_utterance(vars)["text"]
    isno = is_no(state_utils.get_last_human_utterance(vars))
    shared_memory = state_utils.get_shared_memory(vars)
    told_about_cat = shared_memory.get("told_about_cat", False)
    have_cat = re.findall(r"(do|did) you have (a )?(cat)s?", text)
    if (not isno or have_cat) and not told_about_cat:
        flag = True
    logger.info(f"about_cat_request={flag}")
    return flag


def about_dog_request(ngrams, vars):
    flag = False
    text = state_utils.get_last_human_utterance(vars)["text"]
    isno = is_no(state_utils.get_last_human_utterance(vars))
    shared_memory = state_utils.get_shared_memory(vars)
    told_about_dog = shared_memory.get("told_about_dog", False)
    have_dog = re.findall(r"(do|did) you have (a )?(dog)s?", text)
    if (not isno or have_dog) and not told_about_dog:
        flag = True
    logger.info(f"about_dog_request={flag}")
    return flag


def my_cat_1_request(ngrams, vars):
    flag = False
    text = state_utils.get_last_human_utterance(vars)["text"]
    isno = is_no(state_utils.get_last_human_utterance(vars))
    shared_memory = state_utils.get_shared_memory(vars)
    my_pet = shared_memory.get("my_pet", "")
    told_about_cat = shared_memory.get("told_about_cat", False)
    start_about_cat = shared_memory.get("start_about_cat", False)
    have_cat = re.findall(r"(do|did) you have (a )?(cat)s?", text)
    if (not isno or have_cat) and (not told_about_cat or start_about_cat) and my_pet != "dog":
        flag = True
    logger.info(f"my_cat_1_request={flag}")
    return flag


def my_dog_1_request(ngrams, vars):
    flag = False
    text = state_utils.get_last_human_utterance(vars)["text"]
    isno = is_no(state_utils.get_last_human_utterance(vars))
    shared_memory = state_utils.get_shared_memory(vars)
    my_pet = shared_memory.get("my_pet", "")
    told_about_dog = shared_memory.get("told_about_dog", False)
    start_about_dog = shared_memory.get("start_about_dog", False)
    have_dog = re.findall(r"(do|did) you have (a )?(dog)s?", text)
    if (not isno or have_dog) and (not told_about_dog or start_about_dog) and my_pet != "cat":
        flag = True
    logger.info(f"my_dog_1_request={flag}")
    return flag


def my_cat_2_request(ngrams, vars):
    flag = False
    isno = is_no(state_utils.get_last_human_utterance(vars))
    if not isno:
        flag = True
    logger.info(f"my_cat_2_request={flag}")
    return flag


def my_dog_2_request(ngrams, vars):
    flag = False
    isno = is_no(state_utils.get_last_human_utterance(vars))
    if not isno:
        flag = True
    logger.info(f"my_dog_2_request={flag}")
    return flag


def my_cat_3_request(ngrams, vars):
    flag = False
    isno = is_no(state_utils.get_last_human_utterance(vars))
    if not isno:
        flag = True
    logger.info(f"my_cat_3_request={flag}")
    return flag


def my_dog_3_request(ngrams, vars):
    flag = False
    isno = is_no(state_utils.get_last_human_utterance(vars))
    if not isno:
        flag = True
    logger.info(f"my_dog_3_request={flag}")
    return flag


def tell_about_cat_response(vars):
    while True:
        my_pet_info = random.choice(WHAT_PETS_I_HAVE)
        if my_pet_info["pet"] == "cat":
            break
    my_pet = "cat"
    my_pet_name = my_pet_info["name"]
    my_pet_breed = my_pet_info["breed"]
    sentence = my_pet_info["sentence"]
    state_utils.save_to_shared_memory(vars, start_about_cat=True)
    state_utils.save_to_shared_memory(vars, my_pet=my_pet)
    state_utils.save_to_shared_memory(vars, my_pet_name=my_pet_name)
    state_utils.save_to_shared_memory(vars, my_pet_breed=my_pet_breed)
    response = f"{sentence} Would you like to learn more about my {my_pet}?"
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    return response


def tell_about_dog_response(vars):
    while True:
        my_pet_info = random.choice(WHAT_PETS_I_HAVE)
        if my_pet_info["pet"] == "dog":
            break
    my_pet = "dog"
    my_pet_name = my_pet_info["name"]
    my_pet_breed = my_pet_info["breed"]
    sentence = my_pet_info["sentence"]
    state_utils.save_to_shared_memory(vars, start_about_dog=True)
    state_utils.save_to_shared_memory(vars, my_pet=my_pet)
    state_utils.save_to_shared_memory(vars, my_pet_name=my_pet_name)
    state_utils.save_to_shared_memory(vars, my_pet_breed=my_pet_breed)
    response = f"{sentence} Would you like to learn more about my {my_pet}?"
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    return response


def my_cat_1_response(vars):
    fact = MY_CAT[0]
    shared_memory = state_utils.get_shared_memory(vars)
    my_pet_name = shared_memory.get("my_pet_name", "my cat")
    question_cat = random.choice(questions_pets)
    question_cat = question_cat.format(random.choice(["my cat", my_pet_name]))
    response = " ".join([fact, question_cat])
    state_utils.save_to_shared_memory(vars, told_about_cat=True)
    state_utils.save_to_shared_memory(vars, cat=True)
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    logger.info(f"my_cat_1_response: {response}")
    return response


def my_cat_2_response(vars):
    fact = MY_CAT[1]
    shared_memory = state_utils.get_shared_memory(vars)
    my_pet_name = shared_memory.get("my_pet_name", "my cat")
    question_cat = random.choice(questions_pets)
    question_cat = question_cat.format(random.choice(["my cat", my_pet_name]))
    response = " ".join([fact, question_cat])
    state_utils.save_to_shared_memory(vars, cat=True)
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    logger.info(f"my_cat_2_response: {response}")
    return response


def my_cat_3_response(vars):
    fact = MY_CAT[2]
    about_dog = "I also have a dog."
    shared_memory = state_utils.get_shared_memory(vars)
    told_about_dog = shared_memory.get("told_about_dog", False)
    if told_about_dog:
        response = fact
    else:
        response = " ".join([fact, about_dog])
    state_utils.save_to_shared_memory(vars, cat=True)
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    logger.info(f"my_cat_3_response: {response}")
    return response


def my_dog_1_response(vars):
    fact = MY_DOG[0]
    shared_memory = state_utils.get_shared_memory(vars)
    my_pet_name = shared_memory.get("my_pet_name", "my dog")
    question_dog = random.choice(questions_pets)
    question_dog = question_dog.format(random.choice(["my dog", my_pet_name]))
    response = " ".join([fact, question_dog])
    state_utils.save_to_shared_memory(vars, told_about_dog=True)
    state_utils.save_to_shared_memory(vars, dog=True)
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    logger.info(f"my_dog_1_response: {response}")
    return response


def my_dog_2_response(vars):
    fact = MY_DOG[1]
    shared_memory = state_utils.get_shared_memory(vars)
    my_pet_name = shared_memory.get("my_pet_name", "my dog")
    question_dog = random.choice(questions_pets)
    question_dog = question_dog.format(random.choice(["my dog", my_pet_name]))
    response = " ".join([fact, question_dog])
    state_utils.save_to_shared_memory(vars, dog=True)
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    logger.info(f"my_dog_2_response: {response}")
    return response


def my_dog_3_response(vars):
    fact = MY_DOG[2]
    about_cat = "I also have a cat."
    shared_memory = state_utils.get_shared_memory(vars)
    told_about_cat = shared_memory.get("told_about_cat", False)
    if told_about_cat:
        response = fact
    else:
        response = " ".join([fact, about_cat])
    state_utils.save_to_shared_memory(vars, dog=True)
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    logger.info(f"my_dog_3_response: {response}")
    return response


def to_animals_flow_request(ngrams, vars):
    flag = True
    logger.info(f"to_animals_flow_request={flag}")
    return flag


def error_response(vars):
    state_utils.set_confidence(vars, 0)
    return ""


simplified_dialog_flow = dialogflow_extention.DFEasyFilling(MyPetsState.USR_START)

simplified_dialog_flow.add_user_serial_transitions(
    MyPetsState.USR_START,
    {
        MyPetsState.SYS_MY_CAT_1: my_cat_1_request,
        MyPetsState.SYS_MY_DOG_1: my_dog_1_request,
        (scopes.ANIMALS, AnimalsState.USR_START): to_animals_flow_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    MyPetsState.USR_ABOUT_CAT,
    {
        MyPetsState.SYS_MY_CAT_1: my_cat_1_request,
        (scopes.ANIMALS, AnimalsState.USR_START): to_animals_flow_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    MyPetsState.USR_ABOUT_DOG,
    {
        MyPetsState.SYS_MY_DOG_1: my_dog_1_request,
        (scopes.ANIMALS, AnimalsState.USR_START): to_animals_flow_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    MyPetsState.USR_MY_CAT_1,
    {
        MyPetsState.SYS_MY_CAT_2: my_cat_2_request,
        MyPetsState.SYS_ABOUT_DOG: about_dog_request,
        (scopes.ANIMALS, AnimalsState.USR_START): to_animals_flow_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    MyPetsState.USR_MY_DOG_1,
    {
        MyPetsState.SYS_MY_DOG_2: my_dog_2_request,
        MyPetsState.SYS_ABOUT_CAT: about_cat_request,
        (scopes.ANIMALS, AnimalsState.USR_START): to_animals_flow_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    MyPetsState.USR_MY_CAT_2,
    {
        MyPetsState.SYS_MY_CAT_3: my_cat_3_request,
        MyPetsState.SYS_ABOUT_DOG: about_dog_request,
        (scopes.ANIMALS, AnimalsState.USR_START): to_animals_flow_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    MyPetsState.USR_MY_DOG_2,
    {
        MyPetsState.SYS_MY_DOG_3: my_dog_3_request,
        MyPetsState.SYS_ABOUT_CAT: about_cat_request,
        (scopes.ANIMALS, AnimalsState.USR_START): to_animals_flow_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    MyPetsState.USR_MY_CAT_3,
    {
        MyPetsState.SYS_ABOUT_DOG: about_dog_request,
        (scopes.ANIMALS, AnimalsState.USR_START): to_animals_flow_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    MyPetsState.USR_MY_DOG_3,
    {
        MyPetsState.SYS_ABOUT_CAT: about_cat_request,
        (scopes.ANIMALS, AnimalsState.USR_START): to_animals_flow_request,
    },
)

simplified_dialog_flow.add_system_transition(MyPetsState.SYS_ABOUT_CAT, MyPetsState.USR_ABOUT_CAT,
                                             tell_about_cat_response, )
simplified_dialog_flow.add_system_transition(MyPetsState.SYS_ABOUT_DOG, MyPetsState.USR_ABOUT_DOG,
                                             tell_about_dog_response, )
simplified_dialog_flow.add_system_transition(MyPetsState.SYS_MY_CAT_1, MyPetsState.USR_MY_CAT_1, my_cat_1_response, )
simplified_dialog_flow.add_system_transition(MyPetsState.SYS_MY_DOG_1, MyPetsState.USR_MY_DOG_1, my_dog_1_response, )
simplified_dialog_flow.add_system_transition(MyPetsState.SYS_MY_CAT_2, MyPetsState.USR_MY_CAT_2, my_cat_2_response, )
simplified_dialog_flow.add_system_transition(MyPetsState.SYS_MY_DOG_2, MyPetsState.USR_MY_DOG_2, my_dog_2_response, )
simplified_dialog_flow.add_system_transition(MyPetsState.SYS_MY_CAT_3, MyPetsState.USR_MY_CAT_3, my_cat_3_response, )
simplified_dialog_flow.add_system_transition(MyPetsState.SYS_MY_DOG_3, MyPetsState.USR_MY_DOG_3, my_dog_3_response, )
simplified_dialog_flow.add_system_transition(MyPetsState.SYS_ERR, (scopes.MAIN, scopes.State.USR_ROOT),
                                             error_response, )

simplified_dialog_flow.set_error_successor(MyPetsState.USR_START, MyPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(MyPetsState.SYS_ABOUT_CAT, MyPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(MyPetsState.SYS_ABOUT_DOG, MyPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(MyPetsState.USR_ABOUT_CAT, MyPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(MyPetsState.USR_ABOUT_DOG, MyPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(MyPetsState.SYS_MY_CAT_1, MyPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(MyPetsState.SYS_MY_DOG_1, MyPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(MyPetsState.USR_MY_CAT_1, MyPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(MyPetsState.USR_MY_DOG_1, MyPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(MyPetsState.USR_MY_CAT_2, MyPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(MyPetsState.USR_MY_DOG_2, MyPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(MyPetsState.SYS_MY_CAT_2, MyPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(MyPetsState.SYS_MY_DOG_2, MyPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(MyPetsState.SYS_MY_CAT_3, MyPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(MyPetsState.SYS_MY_DOG_3, MyPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(MyPetsState.USR_MY_CAT_3, MyPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(MyPetsState.USR_MY_DOG_3, MyPetsState.SYS_ERR)

dialogflow = simplified_dialog_flow.get_dialogflow()
