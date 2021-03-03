import json
import logging
import random
import re
from CoBotQA.cobotqa_service import send_cobotqa
from enum import Enum, auto

import common.dialogflow_framework.stdm.dialogflow_extention as dialogflow_extention
import common.dialogflow_framework.utils.state as state_utils
from common.universal_templates import if_lets_chat_about_topic, COMPILE_WHAT_TO_TALK_ABOUT
from common.utils import get_intents, is_yes, is_no
from common.animals import PETS_TEMPLATE, COLORS_TEMPLATE, LIKE_ANIMALS_REQUESTS, HAVE_PETS_REQUESTS, \
    OFFER_TALK_ABOUT_ANIMALS

import dialogflows.scopes as scopes

logger = logging.getLogger(__name__)

breeds = json.load(open("breeds.json", 'r'))


class State(Enum):
    USR_START = auto()
    #
    SYS_LETS_TALK_ABOUT = auto()
    SYS_HAVE_PETS = auto()
    SYS_LIKE_ANIMALS = auto()
    SYS_WHAT_ANIMALS = auto()
    SYS_Q_HAVE_PETS = auto()
    SYS_ASK_ABOUT_ZOO = auto()
    SYS_ASK_SOME_QUESTIONS = auto()
    #
    USR_WHAT_ANIMALS = auto()
    USR_TELL_ABOUT_PETS = auto()
    USR_ASK_ABOUT_ZOO = auto()
    USR_HAVE_PETS = auto()
    USR_ASK_SOME_QUESTIONS = auto()
    #
    SYS_IS_WILD = auto()
    SYS_ASK_ABOUT_BREED = auto()
    SYS_ASK_ABOUT_COLOR = auto()
    SYS_ASK_ABOUT_FEEDING = auto()
    SYS_USER_HAS_BEEN = auto()
    SYS_USER_HAS_NOT_BEEN = auto()
    #
    USR_TELL_FACT_ASK_ABOUT_PETS = auto()
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


def lets_talk_about_request(vars):
    ANIMALS_TEMPLATE = re.compile(r"(animals|pets)", re.IGNORECASE)
    uttr = state_utils.get_last_human_utterance(vars)
    user_lets_chat_about = "lets_chat_about" in get_intents(uttr, which="intent_catcher") or if_lets_chat_about_topic(
        uttr["text"]) or re.search(COMPILE_WHAT_TO_TALK_ABOUT, uttr["text"])
    user_lets_chat_about_animals = re.search(ANIMALS_TEMPLATE, uttr["text"]) and not \
        re.search("like|love|have", uttr["text"])
    linkto_talk_about_animals = any([req.lower() in state_utils.get_last_bot_utterance(vars)["text"].lower()
                                     for req in OFFER_TALK_ABOUT_ANIMALS])
    user_agrees = is_yes(state_utils.get_last_human_utterance(vars))

    if (user_lets_chat_about and user_lets_chat_about_animals) or (linkto_talk_about_animals and user_agrees):
        logger.info("lets talk about animals request")
        return True
    return False


def have_pets_request(ngrams, vars):
    flag = False
    text = state_utils.get_last_human_utterance(vars)["text"]
    if re.findall("(do|did) you have (any )?(pets|animals)", text):
        flag = True
    logger.info(f"have_pets_request {flag}")
    return flag


def like_animals_request(ngrams, vars):
    flag = False
    text = state_utils.get_last_human_utterance(vars)["text"]
    if re.findall("(do|did) you (like|love) (pets|animals)", text):
        flag = True
    logger.info(f"like_animals_request {flag}")
    return flag


def sys_what_animals_request(ngrams, vars):
    flag = False
    linkto_like_animals = any([req.lower() in state_utils.get_last_bot_utterance(vars)["text"].lower()
                               for req in LIKE_ANIMALS_REQUESTS])
    user_agrees = is_yes(state_utils.get_last_human_utterance(vars))
    if ("what_animals" not in state_utils.get_used_links(vars) and lets_talk_about_request(vars)) or \
            (linkto_like_animals and user_agrees):
        state_utils.save_used_links(vars, "what_animals")
        flag = True
    logger.info(f"sys_what_animals_request {flag}")
    return flag


def sys_have_pets_request(ngrams, vars):
    flag = False
    if "have_pets" not in state_utils.get_used_links(vars) and lets_talk_about_request(vars):
        state_utils.save_used_links(vars, "have_pets")
        flag = True
    logger.info(f"sys_have_pets_request {flag}")
    return flag


def sys_ask_about_zoo_request(ngrams, vars):
    flag = False
    if "ask_about_zoo" not in state_utils.get_used_links(vars) and lets_talk_about_request(vars):
        state_utils.save_used_links(vars, "ask_about_zoo")
        flag = True
    logger.info(f"sys_ask_about_zoo_request {flag}")
    return flag


def sys_ask_some_questions_request(ngrams, vars):
    flag = False
    if "some_questions" not in state_utils.get_used_links(vars) and lets_talk_about_request(vars):
        state_utils.save_used_links(vars, "some_questions")
        flag = True
    logger.info(f"sys_ask_some_questions_request {flag}")
    return flag


def what_animals_response(vars):
    response = "What animals do you like?"
    return response


def have_pets_response(vars):
    response = "Do you have any pets?"
    return response


def ask_about_zoo_response(vars):
    response = "Have you ever been to the zoo?"
    return response


def ask_some_questions_response(vars):
    questions = ["Do you think that animals dream?", "Have you ever been in the farm?"]
    response = random.choice(questions)
    return response


def tell_about_pets_response(vars):
    responses = ["I have a dog named Jack. He is a German Shepherd. He is very cute.",
                 "I have a cat named Thomas. He is active and playful, enjoying games like fetch and learning tricks."]
    response = random.choice(responses)
    return response


def user_has_been_request(ngrams, vars):
    if is_yes(state_utils.get_last_human_utterance(vars)):
        return True
    return False


def user_has_not_been_request(ngrams, vars):
    if is_no(state_utils.get_last_human_utterance(vars)):
        return True
    return False


def is_wild_request(ngrams, vars):
    flag = False
    text = state_utils.get_last_human_utterance(vars)["text"]
    if not re.findall(PETS_TEMPLATE, text):
        flag = True
    logger.info(f"is_wild_request {flag}")
    return flag


def ask_about_breed_request(ngrams, vars):
    flag = False
    text = state_utils.get_last_human_utterance(vars)["text"]
    linkto_have_pets = any([req.lower() in state_utils.get_last_bot_utterance(vars)["text"].lower()
                            for req in HAVE_PETS_REQUESTS])
    if re.findall(PETS_TEMPLATE, text) and not re.findall("|".join(breeds.keys()), text) and linkto_have_pets:
        flag = True
    logger.info(f"ask_about_breed {flag}")
    return flag


def ask_about_color_request(ngrams, vars):
    flag = False
    text = state_utils.get_last_human_utterance(vars)["text"]
    linkto_have_pets = any([req.lower() in state_utils.get_last_bot_utterance(vars)["text"].lower()
                            for req in HAVE_PETS_REQUESTS])
    if re.findall(PETS_TEMPLATE, text) and not re.findall(COLORS_TEMPLATE, text) and linkto_have_pets:
        flag = True
    logger.info(f"ask_about_color {flag}")
    return flag


def ask_about_feeding_request(ngrams, vars):
    flag = False
    text = state_utils.get_last_human_utterance(vars)["text"]
    if re.findall(PETS_TEMPLATE, text) and "feed" not in text:
        flag = True
    logger.info(f"ask_about_feeding {flag}")
    return flag


def ask_more_details_response(vars):
    response = "What is your impression?"
    return response


def suggest_visiting_response(vars):
    response = "A day at the zoo also encourages a healthy lifestyle while bringing family and friends together." + \
               "It is the perfect day trip destination for any season!"
    return response


def tell_fact_ask_about_pets_response(vars):
    annotations = state_utils.get_last_human_utterance(vars)["annotations"]
    nounphr = annotations.get("cobot_nounphrases", [])
    fact = ""
    if nounphr:
        fact = send_cobotqa(f"fact about {nounphr[0]}")
    ask_about_pets = "Do you have pets?"
    response = " ".join([fact, ask_about_pets])
    return response


def ask_about_breed_response(vars):
    response = "What breed is it?"
    return response


def ask_about_color_response(vars):
    response = "What color is it?"
    return response


def ask_about_feeding_response(vars):
    response = "How do you feed him?"
    return response


def tell_fact_about_breed_request(ngrams, vars):
    text = state_utils.get_last_human_utterance(vars)["text"]
    if re.findall("|".join(breeds.keys()), text):
        return True
    return False


def ask_about_training_request(ngrams, vars):
    return True


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
        response = "They are sensitive and intelligent dogs, known for undying loyalty and the amazing ability to" + \
                   "foresee their owners’ needs."
    return response


def ask_about_training_response(vars):
    response = "Did you train him to execute commands?"
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
    },
)
simplified_dialog_flow.set_error_successor(State.USR_START, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.SYS_WHAT_ANIMALS, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.SYS_Q_HAVE_PETS, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.SYS_ASK_ABOUT_ZOO, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.SYS_ASK_SOME_QUESTIONS, State.SYS_ERR)

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
    State.SYS_LIKE_ANIMALS,
    State.USR_TELL_ABOUT_PETS,
    tell_about_pets_response,
)
simplified_dialog_flow.set_error_successor(State.SYS_LIKE_ANIMALS, State.SYS_ERR)

simplified_dialog_flow.add_user_serial_transitions(
    State.USR_WHAT_ANIMALS,
    {
        State.SYS_IS_WILD: is_wild_request,
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
    State.SYS_IS_WILD,
    State.USR_TELL_FACT_ASK_ABOUT_PETS,
    tell_fact_ask_about_pets_response,
)
simplified_dialog_flow.set_error_successor(State.SYS_IS_WILD, State.SYS_ERR)

simplified_dialog_flow.add_system_transition(
    State.SYS_ASK_ABOUT_BREED,
    State.USR_ASK_ABOUT_BREED,
    ask_about_breed_response,
)
simplified_dialog_flow.set_error_successor(State.SYS_ASK_ABOUT_BREED, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.USR_ASK_ABOUT_BREED, State.SYS_ERR)

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
    State.USR_ASK_ABOUT_BREED,
    {
        State.SYS_TELL_FACT_ABOUT_BREED: tell_fact_about_breed_request,
        State.SYS_ASK_ABOUT_TRAINING: ask_about_training_request,
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

simplified_dialog_flow.add_user_transition(
    State.USR_TELL_FACT_ASK_ABOUT_PETS,
    State.SYS_HAVE_PETS,
    have_pets_request,
)
simplified_dialog_flow.add_user_transition(
    State.USR_ASK_ABOUT_BREED,
    State.SYS_HAVE_PETS,
    have_pets_request,
)
simplified_dialog_flow.add_user_transition(
    State.USR_ASK_ABOUT_COLOR,
    State.SYS_HAVE_PETS,
    have_pets_request,
)
simplified_dialog_flow.add_user_transition(
    State.USR_ASK_ABOUT_FEEDING,
    State.SYS_HAVE_PETS,
    have_pets_request,
)

# cycle transitions to State.SYS_LIKE_ANIMALS

simplified_dialog_flow.add_user_transition(
    State.USR_ASK_SOME_QUESTIONS,
    State.SYS_LIKE_ANIMALS,
    like_animals_request,
)
simplified_dialog_flow.add_user_transition(
    State.USR_TELL_FACT_ASK_ABOUT_PETS,
    State.SYS_LIKE_ANIMALS,
    like_animals_request,
)
simplified_dialog_flow.add_user_transition(
    State.USR_ASK_ABOUT_BREED,
    State.SYS_LIKE_ANIMALS,
    like_animals_request,
)
simplified_dialog_flow.add_user_transition(
    State.USR_ASK_ABOUT_COLOR,
    State.SYS_LIKE_ANIMALS,
    like_animals_request,
)
simplified_dialog_flow.add_user_transition(
    State.USR_ASK_ABOUT_FEEDING,
    State.SYS_LIKE_ANIMALS,
    like_animals_request,
)

simplified_dialog_flow.add_system_transition(
    State.SYS_ERR,
    (scopes.MAIN, scopes.State.USR_ROOT),
    error_response,
)

dialogflow = simplified_dialog_flow.get_dialogflow()
