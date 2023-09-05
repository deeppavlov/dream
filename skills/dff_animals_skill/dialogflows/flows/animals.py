import logging
import random
import os
import re
import en_core_web_sm
import inflect
import sentry_sdk

import common.constants as common_constants
from dff import dialogflow_extension
import common.dialogflow_framework.utils.state as state_utils
from common.dialogflow_framework.utils.condition import if_was_prev_active
from common.dialogflow_framework.utils.condition import get_last_state
from common.utils import is_yes, is_no
from common.universal_templates import if_chat_about_particular_topic, if_lets_chat, NOT_LIKE_PATTERN
from common.animals import (
    PETS_TEMPLATE,
    PETS_TEMPLATE_EXT,
    ANIMALS_FIND_TEMPLATE,
    LIKE_ANIMALS_REQUESTS,
    WILD_ANIMALS,
    WHAT_PETS_I_HAVE,
    HAVE_LIKE_PETS_TEMPLATE,
    TRIGGER_PHRASES,
    NOT_SWITCH_TEMPLATE,
    DO_YOU_HAVE_TEMPLATE,
    ANIMAL_BADLIST,
)
from common.wiki_skill import if_linked_to_wiki_skill
from common.animals import stop_about_animals, find_entity_by_types, find_entity_conceptnet

import dialogflows.scopes as scopes
from dialogflows.flows.my_pets_states import State as MyPetsState
from dialogflows.flows.user_pets_states import State as UserPetsState
from dialogflows.flows.wild_animals_states import State as WildAnimalsState
from dialogflows.flows.animals_states import State as AS
from dialogflows.flows.animals_utils import find_in_animals_list

sentry_sdk.init(os.getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)

nlp = en_core_web_sm.load()
p = inflect.engine()

CONF_1 = 1.0
CONF_2 = 0.98
CONF_3 = 0.95
CONF_4 = 0.9


def if_link_from_wiki_skill(vars):
    flag = False
    cross_link = state_utils.get_cross_link(vars, service_name="dff_animals_skill")
    from_skill = cross_link.get("from_service", "")
    if from_skill == "dff_wiki_skill":
        flag = True
    logger.info(f"if_link_from_wiki_skill {cross_link}")
    return flag


def activate_after_wiki_skill(vars):
    flag = False
    cross_link = state_utils.get_cross_link(vars, service_name="dff_animals_skill")
    from_skill = cross_link.get("from_service", "")
    isno = is_no(state_utils.get_last_human_utterance(vars))
    if from_skill == "dff_wiki_skill" and isno:
        flag = True
    return flag


def is_last_state(vars, state):
    prev_state = get_last_state(vars)
    return str(prev_state).split(".")[-1] == state


def make_my_pets_info(vars, rnd=True):
    shared_memory = state_utils.get_shared_memory(vars)
    my_pets_info = shared_memory.get("my_pets_info", {})
    if not my_pets_info:
        if rnd:
            random.shuffle(WHAT_PETS_I_HAVE)
        for pet in ["cat", "dog"]:
            for elem in WHAT_PETS_I_HAVE:
                if elem["pet"] == pet:
                    my_pets_info[pet] = {"name": elem["name"], "breed": elem["breed"], "sentence": elem["sentence"]}
                    break
        state_utils.save_to_shared_memory(vars, my_pets_info=my_pets_info)


def stop_animals_request(ngrams, vars):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    bot_uttr = state_utils.get_last_human_utterance(vars)
    found_prompt = any([phrase.lower() in bot_uttr["text"].lower() for phrase in TRIGGER_PHRASES])
    isno = is_no(user_uttr)
    shared_memory = state_utils.get_shared_memory(vars)
    if stop_about_animals(user_uttr, shared_memory):
        flag = True
    if found_prompt and not isno:
        flag = False
    logger.info(f"stop_animals_request={flag}")
    return flag


def lets_talk_about_request(vars):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    have_pets = re.search(HAVE_LIKE_PETS_TEMPLATE, user_uttr["text"])
    found_prompt = any([phrase.lower() in bot_uttr["text"].lower() for phrase in TRIGGER_PHRASES])
    isno = is_no(user_uttr)
    is_stop = re.findall(r"(stop|shut|something else|change|don't want)", user_uttr["text"])
    chat_about = if_chat_about_particular_topic(user_uttr, bot_uttr, compiled_pattern=ANIMALS_FIND_TEMPLATE)
    find_pattern = re.findall(ANIMALS_FIND_TEMPLATE, user_uttr["text"])
    dont_like = re.findall(NOT_LIKE_PATTERN, user_uttr["text"])
    was_prev_active = if_was_prev_active(vars)
    if chat_about and find_pattern:
        flag = True
    if not dont_like and (
        have_pets
        or (find_pattern and (not is_last_state(vars, "SYS_WHAT_ANIMALS") or not was_prev_active))
        or (found_prompt and not isno and not is_stop)
    ):
        flag = True
    if re.findall(NOT_SWITCH_TEMPLATE, user_uttr["text"]):
        flag = False
    logger.info(f"lets_talk_about_request={flag}")
    return flag


def user_asked_have_pets_request(ngrams, vars):
    flag = False
    shared_memory = state_utils.get_shared_memory(vars)
    user_uttr = state_utils.get_last_human_utterance(vars)
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    annotations = state_utils.get_last_human_utterance(vars)["annotations"]
    have_pet = re.findall(
        r"(do|did|have) you (have |had |like )?(any |a )?(pets|pet|animals|animal|dog|cat|puppy|" r"kitty|kitten)",
        user_uttr["text"],
    )
    tell_about_pet = re.findall(r"(tell|talk|hear)(.*)(your )(dog|cat|puppy|kitty|kitten)s?", user_uttr["text"])
    users_pet = re.findall(r"my (cat|dog|puppy|kitty|kitten|rat|fish|parrot|hamster)", user_uttr["text"], re.IGNORECASE)
    user_has_pet = re.findall(
        r"i (have |had )(a )?(cat|dog|puppy|kitty|kitten|rat|fish|parrot|hamster)", user_uttr["text"], re.IGNORECASE
    )
    found_animal = find_entity_by_types(annotations, {"Q55983715", "Q16521"})
    pet_mentioned = re.findall(r"(cat|dog|puppy|kitty|kitten)", user_uttr["text"], re.IGNORECASE)
    started = shared_memory.get("start", False)
    bot_asked_pet = re.findall(DO_YOU_HAVE_TEMPLATE, bot_uttr["text"])
    isno = is_no(user_uttr)

    if (
        have_pet
        or tell_about_pet
        or (started and not users_pet and not user_has_pet and (not found_animal or pet_mentioned))
        or (bot_asked_pet and isno)
    ):
        flag = True
    if re.findall(NOT_SWITCH_TEMPLATE, user_uttr["text"]):
        flag = False
    logger.info(f"user_asked_have_pets_request={flag}")
    return flag


def user_likes_animal_request(ngrams, vars):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    annotations = user_uttr["annotations"]
    found_animal_cnet = find_entity_conceptnet(annotations, ["animal"])
    found_animal_wp = find_entity_by_types(annotations, {"Q55983715", "Q16521"})
    found_animal_in_list = find_in_animals_list(annotations)
    found_pet = re.search(PETS_TEMPLATE, user_uttr["text"])
    found_badlist = re.findall(NOT_SWITCH_TEMPLATE, user_uttr["text"])
    if (
        not found_pet
        and (found_animal_cnet or (found_animal_wp and found_animal_wp not in ANIMAL_BADLIST) or found_animal_in_list)
        and not is_last_state(vars, "SYS_WHAT_ANIMALS")
        and not found_badlist
    ):
        flag = True
    logger.info(f"user_likes_animal_request={flag}")
    return flag


def mention_pets_request(ngrams, vars):
    flag = False
    text = state_utils.get_last_human_utterance(vars)["text"]
    shared_memory = state_utils.get_shared_memory(vars)
    started = shared_memory.get("start", False)
    dont_like = re.findall(NOT_LIKE_PATTERN, text)
    found_badlist = re.findall(NOT_SWITCH_TEMPLATE, text)
    if re.search(PETS_TEMPLATE, text) and not started and not dont_like and not found_badlist:
        flag = True
    logger.info(f"mention_pets_request={flag}")
    return flag


def user_mentioned_his_pet_request(ngrams, vars):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    isyes = is_yes(user_uttr)
    users_pet = re.findall(r"my (cat|dog|puppy|kitty|kitten)", user_uttr["text"], re.IGNORECASE)
    has_pet = re.findall(r"i (have |had )(a )?(cat|dog|puppy|kitty|kitten)", user_uttr["text"], re.IGNORECASE)
    found_badlist = re.findall(NOT_SWITCH_TEMPLATE, user_uttr["text"])
    bot_asked_pet = "do you have pets" in bot_uttr["text"].lower()
    found_pet = re.search(PETS_TEMPLATE, user_uttr["text"])
    if (users_pet or has_pet or (bot_asked_pet and (found_pet or isyes))) and not found_badlist:
        flag = True
    logger.info(f"user_mentioned_his_pet_request={flag}")
    return flag


def do_you_have_pets_request(ngrams, vars):
    flag = False
    shared_memory = state_utils.get_shared_memory(vars)
    asked_have_pets = shared_memory.get("asked_have_pets", False)
    user_uttr = state_utils.get_last_human_utterance(vars)
    pet_in_uttr = re.findall(r"(\bpet\b|\bpets\b)", user_uttr["text"], re.IGNORECASE)
    found_badlist = re.findall(NOT_SWITCH_TEMPLATE, user_uttr["text"])
    if (
        not found_badlist
        and pet_in_uttr
        and not asked_have_pets
        and ("you" not in user_uttr["text"] or "my" in user_uttr["text"])
    ):
        flag = True
    return flag


def do_you_have_pets_response(vars):
    response = random.choice(
        [
            "I think that pets are a great source of entertainment. Do you have pets at home?",
            "We all know that pets are remarkable for their capacity to love. Do you have pets " "at home?",
        ]
    )
    state_utils.save_to_shared_memory(vars, asked_have_pets=True)
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars, continue_flag=common_constants.MUST_CONTINUE)
    return response


def sys_what_animals_request(ngrams, vars):
    flag = False
    linkto_like_animals = any(
        [req.lower() in state_utils.get_last_bot_utterance(vars)["text"].lower() for req in LIKE_ANIMALS_REQUESTS]
    )
    text = state_utils.get_last_human_utterance(vars)["text"]
    user_agrees = is_yes(state_utils.get_last_human_utterance(vars))
    check_linkto = lets_talk_about_request(vars) or (linkto_like_animals and user_agrees) or text == "animals"
    find_pets = re.findall(r"(\bpet\b|\bpets\b)", text) or re.search(PETS_TEMPLATE, text)
    if check_linkto and not find_pets:
        flag = True
    logger.info(f"sys_what_animals_request={flag}")
    return flag


def is_wild_request(ngrams, vars):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    text = user_uttr["text"]
    annotations = user_uttr["annotations"]
    shared_memory = state_utils.get_shared_memory(vars)
    used_is_wild = shared_memory.get("is_wild", False)
    if (
        not re.search(PETS_TEMPLATE, text)
        and not used_is_wild
        and not if_linked_to_wiki_skill(annotations, "dff_animals_skill")
    ):
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
    bot_uttr = state_utils.get_last_bot_utterance(vars)["text"].lower()
    isno = is_no(state_utils.get_last_human_utterance(vars))
    isyes = is_yes(state_utils.get_last_human_utterance(vars))
    user_has = re.findall("i (have|had)", user_uttr)
    bot_asked_like = "do you like animals" in bot_uttr
    bot_asked_have = "do you have pets" in bot_uttr
    if (
        (re.search(PETS_TEMPLATE_EXT, user_uttr) and not isno)
        or (re.search(PETS_TEMPLATE_EXT, bot_uttr) and (isyes or user_has))
        or (bot_asked_like and user_has)
        or (bot_asked_have and isyes)
    ):
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
    if not isno or if_link_from_wiki_skill(vars):
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
    dont_like = re.findall(NOT_LIKE_PATTERN, text)
    is_wild = shared_memory.get("is_wild", False)
    what_wild = shared_memory.get("what_wild", False)
    logger.info(f"what_wild_request, is wild {is_wild}, what wild {what_wild}")
    started = shared_memory.get("start", False)
    if (
        dont_like
        or is_wild
        or what_wild
        or user_asks_about_pets
        or (not lets_talk_about_request(vars) and not started)
        and not is_last_state(vars, "SYS_WHAT_ANIMALS")
    ):
        flag = False
    if if_lets_chat(text) and not lets_talk_about_request(vars) or if_link_from_wiki_skill(vars):
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
    make_my_pets_info(vars, rnd=False)
    what_i_like = random.choice(WILD_ANIMALS)
    response = f"{what_i_like} What animals do you like?"
    state_utils.set_cross_link(vars, to_service_name="dff_wiki_skill", from_service_name="dff_animals_skill")
    state_utils.save_to_shared_memory(vars, start=True)
    state_utils.save_to_shared_memory(vars, what_animals=True)
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars, continue_flag=common_constants.MUST_CONTINUE)
    return response


def mention_pets_response(vars):
    make_my_pets_info(vars)
    replace_plural = {
        "cats": "cat",
        "dogs": "dog",
        "rats": "rat",
        "puppy": "dog",
        "puppies": "dog",
        "kitty": "cat",
        "kitties": "cat",
    }
    text = state_utils.get_last_human_utterance(vars)["text"]
    pet = re.findall(PETS_TEMPLATE, text)
    if pet[0] in replace_plural:
        found_pet = replace_plural[pet[0]]
    else:
        found_pet = pet[0]
    response = f"Do you have a {found_pet}?"
    state_utils.save_to_shared_memory(vars, start=True)
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars, continue_flag=common_constants.MUST_CONTINUE)
    return response


def what_wild_response(vars):
    make_my_pets_info(vars)
    what_i_like = random.choice(WILD_ANIMALS)
    response = f"{what_i_like} What wild animals do you like?"
    state_utils.save_to_shared_memory(vars, start=True)
    state_utils.save_to_shared_memory(vars, what_wild=True)
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars, continue_flag=common_constants.MUST_CONTINUE)
    return response


def error_response(vars):
    state_utils.save_to_shared_memory(vars, start=False)
    state_utils.set_confidence(vars, 0)
    return ""


simplified_dialog_flow = dialogflow_extension.DFEasyFilling(AS.USR_START)

simplified_dialog_flow.add_user_serial_transitions(
    AS.USR_START,
    {
        AS.SYS_ERR: stop_animals_request,
        AS.SYS_DO_YOU_HAVE: do_you_have_pets_request,
        (scopes.MY_PETS, MyPetsState.USR_START): user_asked_have_pets_request,
        (scopes.USER_PETS, UserPetsState.USR_START): user_mentioned_his_pet_request,
        AS.SYS_WHAT_ANIMALS: sys_what_animals_request,
        (scopes.WILD_ANIMALS, WildAnimalsState.SYS_ANIMAL_Q): user_likes_animal_request,
        AS.SYS_WHAT_WILD_ANIMALS: what_wild_request,
        AS.SYS_MENTION_PETS: mention_pets_request,
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
        (scopes.MY_PETS, MyPetsState.USR_START): user_has_not_pets_request,
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

simplified_dialog_flow.add_system_transition(
    AS.SYS_WHAT_ANIMALS,
    AS.USR_WHAT_ANIMALS,
    what_animals_response,
)
simplified_dialog_flow.add_system_transition(
    AS.SYS_DO_YOU_HAVE,
    AS.USR_HAVE_PETS,
    do_you_have_pets_response,
)
simplified_dialog_flow.add_system_transition(
    AS.SYS_WHAT_WILD_ANIMALS,
    AS.USR_WHAT_WILD_ANIMALS,
    what_wild_response,
)
simplified_dialog_flow.add_system_transition(
    AS.SYS_MENTION_PETS,
    AS.USR_MENTION_PETS,
    mention_pets_response,
)
simplified_dialog_flow.add_system_transition(
    AS.SYS_ERR,
    (scopes.MAIN, scopes.State.USR_ROOT),
    error_response,
)

simplified_dialog_flow.set_error_successor(AS.USR_START, AS.SYS_ERR)
simplified_dialog_flow.set_error_successor(AS.SYS_WHAT_ANIMALS, AS.SYS_ERR)
simplified_dialog_flow.set_error_successor(AS.USR_WHAT_ANIMALS, AS.SYS_ERR)
simplified_dialog_flow.set_error_successor(AS.SYS_WHAT_WILD_ANIMALS, AS.SYS_ERR)
simplified_dialog_flow.set_error_successor(AS.USR_WHAT_WILD_ANIMALS, AS.SYS_ERR)
simplified_dialog_flow.set_error_successor(AS.SYS_MENTION_PETS, AS.SYS_ERR)
simplified_dialog_flow.set_error_successor(AS.USR_MENTION_PETS, AS.SYS_ERR)

dialogflow = simplified_dialog_flow.get_dialogflow()
