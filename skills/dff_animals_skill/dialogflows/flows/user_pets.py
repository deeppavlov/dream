import json
import logging
import random
import os
import re
import sentry_sdk

import common.constants as common_constants
import common.dialogflow_framework.stdm.dialogflow_extention as dialogflow_extention
import common.dialogflow_framework.utils.state as state_utils
import common.dialogflow_framework.utils.condition as condition_utils
from common.utils import is_no, is_yes
import dialogflows.scopes as scopes
from dialogflows.flows.user_pets_states import State as UserPetsState
from dialogflows.flows.animals_states import State as AnimalsState
from dialogflows.flows.animals import make_my_pets_info
from common.animals import PETS_TEMPLATE, CATS_DOGS_PHRASES, stop_about_animals, pet_games, breed_replace_dict

sentry_sdk.init(os.getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

CONF_1 = 1.0
CONF_2 = 0.99
CONF_3 = 0.95

breeds_dict = {}

try:
    with open("/root/.deeppavlov/downloads/wikidata/breed_facts.json", 'r') as fl:
        breeds_dict = json.load(fl)
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)


def extract_pet(utt):
    fnd = re.findall(r"(cat|dog|rat|fish|parrot|hamster)", utt)
    if fnd:
        pet = fnd[0]
    else:
        pet = ""
    return pet


def delete_pet(vars):
    user_uttr = state_utils.get_last_human_utterance(vars)
    user_text = user_uttr["text"]
    shared_memory = state_utils.get_shared_memory(vars)
    users_pet = shared_memory.get("users_pet", "")
    found_pet = re.findall("(don't|do not) have (a )?(cat|dog|rat|fish|parrot|hamster)", user_text)
    if found_pet:
        pet = found_pet[0][2]
        if pet == users_pet:
            state_utils.save_to_shared_memory(vars, users_pet="")
            state_utils.save_to_shared_memory(vars, users_pet_name="")
            state_utils.save_to_shared_memory(vars, users_pet_breed="")


def retrieve_and_save(vars):
    user_uttr = state_utils.get_last_human_utterance(vars)["text"]
    bot_uttr = state_utils.get_last_bot_utterance(vars)["text"]
    isyes = is_yes(state_utils.get_last_human_utterance(vars))
    shared_memory = state_utils.get_shared_memory(vars)
    found_users_pet = shared_memory.get("users_pet", "")
    found_pet_bot_uttr = []
    if not found_users_pet:
        found_users_pet = extract_pet(user_uttr)
        found_pet_bot_uttr = re.findall(r"(do you have a )(cat|dog|rat|fish|parrot|hamster)", bot_uttr, re.IGNORECASE)
        if found_users_pet:
            state_utils.save_to_shared_memory(vars, users_pet=found_users_pet)
        elif found_pet_bot_uttr and isyes:
            state_utils.save_to_shared_memory(vars, users_pet=found_pet_bot_uttr[0][1])
            found_users_pet = found_pet_bot_uttr[0][1]
    logger.info(f"retrieve_and_save, found_users_pet {found_users_pet} found_pet_bot_uttr {found_pet_bot_uttr}"
                f" isyes {isyes}")
    return found_users_pet


def retrieve_and_save_name(vars):
    user_text = state_utils.get_last_human_utterance(vars)["text"]
    shared_memory = state_utils.get_shared_memory(vars)
    annotations = state_utils.get_last_human_utterance(vars)["annotations"]
    ner = annotations.get("ner", [])
    users_pet_breed = shared_memory.get("users_pet_breed", "")
    found_name = ""
    for entities in ner:
        if entities:
            for entity in entities:
                if entity.get("type", "") == "PER":
                    found_name = entity["text"]

    if not found_name:
        fnd = re.findall(r"(name is |named |called |call him |call her )([a-z]+)\b", user_text)
        if fnd:
            found_name = fnd[0][1]

    if found_name and not shared_memory.get("users_pet_name", "") \
            and found_name not in {"black", "white", "grey", "brown", "yellow", "cat", "dog"} \
            and found_name not in users_pet_breed:
        state_utils.save_to_shared_memory(vars, users_pet_name=found_name)

    return found_name


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


def extract_breed(vars):
    shared_memory = state_utils.get_shared_memory(vars)
    found_breed = shared_memory.get("users_pet_breed", "")
    if not found_breed:
        breed_titles = set(breeds_dict.keys())
        user_uttr = state_utils.get_last_human_utterance(vars)
        annotations = user_uttr["annotations"]
        nounphrases = annotations.get("cobot_entities", {}).get("entities", []) + \
            annotations.get("cobot_nounphrases", [])
        nounphrases = list(set(nounphrases))
        nounphrases = [re.sub(r"(cat|cats|dog|dogs)", "", phr).replace("  ", " ").strip() for phr in nounphrases]
        nounphrases = [phr for phr in nounphrases if len(phr) > 2]
        found_breed = ""
        if nounphrases:
            for phr in nounphrases:
                phr = breed_replace_dict.get(phr, phr)
                if phr in breed_titles:
                    found_breed = phr
                    break
            if not found_breed:
                for phr in nounphrases:
                    phr = breed_replace_dict.get(phr, phr)
                    phr_tokens = set(phr.split())
                    for title in breed_titles:
                        title_tokens = set(title.split())
                        if phr_tokens.intersection(title_tokens):
                            found_breed = title
                            break
                    if found_breed:
                        break
        if found_breed:
            state_utils.save_to_shared_memory(vars, users_pet_breed=found_breed)
    return found_breed


def make_utt_with_ack(vars, cur_state):
    ack = ""
    statement = ""
    question = ""
    user_uttr = state_utils.get_last_human_utterance(vars)
    shared_memory = state_utils.get_shared_memory(vars)
    make_my_pets_info(vars)
    prev_state = condition_utils.get_last_state(vars)
    isno = is_no(state_utils.get_last_human_utterance(vars))
    users_pet = shared_memory.get("users_pet", "")
    users_pet_name = shared_memory.get("users_pet_name", "")
    users_pet_breed = shared_memory.get("users_pet_breed", "")
    logger.info(f"make_utt_with_ack users_pet {users_pet} users_pet_name {users_pet_name} "
                f"users_pet_breed {users_pet_breed} {breeds_dict.get('users_pet_breed', '')} "
                f"is_last_state {condition_utils.is_last_state(vars, UserPetsState.SYS_ASK_ABOUT_NAME)}")
    my_pets_info = shared_memory.get("my_pets_info", {})
    if str(prev_state).split('.')[-1] == "SYS_ASK_ABOUT_NAME" and users_pet_name:
        ack = "Very cool name! You have such an amusing mind!"
    if str(prev_state).split('.')[-1] == "SYS_WHAT_BREED":
        if users_pet and users_pet_breed:
            breed_info = breeds_dict[users_pet_breed]
            facts = breed_info.get("facts", "")
            if not facts.endswith("."):
                facts = f"{facts}."
            if facts:
                ack = f"I know a lot about {users_pet} breeds. {facts}"
                #      + f"Would you like to know more about {users_pet_breed}?"
    if str(prev_state).split('.')[-1] == "SYS_PLAY_WITH_PET":
        if not isno:
            ack = "Really, playing with a pet makes a lot of fun."
    if cur_state == UserPetsState.SYS_ASK_ABOUT_NAME:
        if users_pet in {"cat", "dog"}:
            statement = choose_pet_phrase(vars, users_pet)
        if users_pet:
            question = f"What is your {users_pet}'s name?"
        else:
            question = f"What is your pet's name?"
    if cur_state == UserPetsState.SYS_WHAT_BREED:
        if users_pet in {"cat", "dog"}:
            my_pet = my_pets_info[users_pet]
            my_pet_breed = my_pet["breed"]
            statement = f"I have a {my_pet_breed} {users_pet}."
            question = f"What is your {users_pet}'s breed?"
    if cur_state == UserPetsState.SYS_PLAY_WITH_PET:
        if users_pet in {"cat", "dog"}:
            games = " and ".join(pet_games[users_pet])
            statement = f"I like to play with my {users_pet} different games, such as {games}."
        if users_pet:
            question = f"Do you play with your {users_pet}?"
    if cur_state == UserPetsState.SYS_LIKE_PET:
        statement = "There's an old saying that pets repay the love you give them ten-fold."
        if users_pet_name:
            question = f"Do you like {users_pet_name}?"
        elif users_pet:
            question = f"Do you like your {users_pet}?"
        else:
            question = "Do you like your pet?"
    if cur_state == UserPetsState.SYS_ASK_MORE_INFO:
        if users_pet_name and users_pet:
            statement = f"I am very curious about {users_pet_name}."
            question = f"Could you tell me more about your {users_pet}?"
        elif users_pet:
            statement = f"I am very curious about your {users_pet}."
            question = "Could you tell me more about your pet?"
        else:
            statement = "Very interesting!"
            question = "Could you tell me more about your pet?"
    if "bark" in user_uttr["text"]:
        ack = f"Woof-woof, bow-bow, ruff-ruff! {ack}"
    response = f"{ack} {statement} {question}"
    response = response.replace("  ", " ").strip()
    return response


def stop_animals_request(ngrams, vars):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    shared_memory = state_utils.get_shared_memory(vars)
    stop_about_animals(user_uttr, shared_memory)
    if stop_about_animals(user_uttr, shared_memory):
        flag = True
    logger.info(f"stop_animals_request={flag}")
    return flag


def what_pets_request(ngrams, vars):
    flag = False
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    user_uttr = state_utils.get_last_human_utterance(vars)
    isyes = is_yes(state_utils.get_last_human_utterance(vars))
    user_has = re.findall(r"i (have|had)", user_uttr["text"])
    mention_pet = re.findall(PETS_TEMPLATE, user_uttr["text"])
    asked_about_pets = "do you have pets" in bot_uttr["text"].lower()
    bot_asked_pet = re.findall(r"do you have a (cat|dog|rat|fish|parrot|hamster)", bot_uttr["text"], re.IGNORECASE)
    logger.info(f"what_pets_request, {asked_about_pets}, {isyes}, {user_has}, {mention_pet}")
    if asked_about_pets and (isyes or user_has) and not mention_pet and not (bot_asked_pet and is_yes):
        flag = True
    logger.info(f"what_pets_request={flag}")
    return flag


def ask_about_name_request(ngrams, vars):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    isno = is_no(state_utils.get_last_human_utterance(vars))
    isyes = is_yes(state_utils.get_last_human_utterance(vars))
    user_has = re.findall(r"i (have|had)", user_uttr["text"])
    extract_breed(vars)
    delete_pet(vars)
    bot_asked_pet = re.findall(r"do you have a (cat|dog|rat|fish|parrot|hamster)", bot_uttr["text"], re.IGNORECASE)
    user_has_not = (bot_asked_pet and isno) and not re.findall(PETS_TEMPLATE, user_uttr["text"])
    user_told_pet = re.findall("(cat|dog|rat|fish|parrot|hamster)", user_uttr["text"]) \
        and re.findall(r"(do you have pets|what pets do you have)", bot_uttr["text"], re.IGNORECASE)
    user_mentioned_pet = re.findall(r"my (cat|dog|rat|fish|parrot|hamster)", user_uttr["text"])
    shared_memory = state_utils.get_shared_memory(vars)
    asked_name = shared_memory.get("asked_name", False)
    users_pet = shared_memory.get("users_pet", "")
    users_pet_name = shared_memory.get("users_pet_name", "")
    logger.info(f"ask_about_name, users_pet {users_pet} bot_asked_pet {bot_asked_pet} user_told_pet {user_told_pet}")
    if not users_pet_name and not user_has_not and not asked_name \
            and not re.findall(r"(name|call)", user_uttr["text"]) \
            and (users_pet or (bot_asked_pet and (isyes or user_has)) or user_told_pet or user_mentioned_pet):
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
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    user_uttr = state_utils.get_last_human_utterance(vars)
    user_mention_pet = re.findall(r"\b(cat|dog)s?\b", user_uttr["text"])
    user_has = re.findall(r"\b(have|had)\b", user_uttr["text"])
    asked_like = "what animals do you like" in bot_uttr["text"].lower()
    delete_pet(vars)
    if asked_like and user_mention_pet and not user_has:
        flag = True
    logger.info(f"is_dog_cat_request={flag}")
    return flag


def ask_about_breed_request(ngrams, vars):
    flag = False
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    user_uttr = state_utils.get_last_human_utterance(vars)
    shared_memory = state_utils.get_shared_memory(vars)
    found_pet = re.findall(PETS_TEMPLATE, user_uttr["text"])
    delete_pet(vars)
    users_pet = shared_memory.get("users_pet", "")
    users_pet_name = shared_memory.get("users_pet_name", "")
    isyes = is_yes(state_utils.get_last_human_utterance(vars))
    user_has = re.findall(r"i (have|had)", user_uttr["text"])
    bot_asked_pet = re.findall(r"do you have a (cat|dog|rat|fish|parrot|hamster)", bot_uttr["text"], re.IGNORECASE)
    asked_breed = shared_memory.get("asked_breed", False)
    found_breed = extract_breed(vars)
    isno = is_no(state_utils.get_last_human_utterance(vars))
    user_has_not = (re.findall("do you have a (cat|dog)", bot_uttr["text"], re.IGNORECASE) and isno) and not \
        re.findall(PETS_TEMPLATE, user_uttr["text"])
    logger.info(f"ask_about_breed_request_isno {isno}")
    if not user_has_not and not asked_breed \
            and (found_pet or users_pet_name or users_pet or (bot_asked_pet and (isyes or user_has))) \
            and not found_breed:
        flag = True
    if (users_pet and users_pet not in {"cat", "dog"}) or (found_pet and found_pet[0] not in {"cat", "dog"}):
        flag = False
    logger.info(f"ask_about_breed_request={flag}")
    return flag


def ask_about_playing_request(ngrams, vars):
    flag = False
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    user_uttr = state_utils.get_last_human_utterance(vars)
    shared_memory = state_utils.get_shared_memory(vars)
    found_pet = re.findall(PETS_TEMPLATE, user_uttr["text"])
    delete_pet(vars)
    users_pet = shared_memory.get("users_pet", "")
    users_pet_name = shared_memory.get("users_pet_name", "")
    isyes = is_yes(state_utils.get_last_human_utterance(vars))
    user_has = re.findall(r"i (have|had)", user_uttr["text"])
    bot_asked_pet = re.findall(r"do you have a (cat|dog|rat|fish|parrot|hamster)", bot_uttr["text"], re.IGNORECASE)
    asked_play = shared_memory.get("asked_play", False)
    found_play = "play" in user_uttr["text"]
    isno = is_no(state_utils.get_last_human_utterance(vars))
    user_has_not = (re.findall("do you have a (cat|dog|rat|fish|parrot|hamster)", bot_uttr["text"], re.IGNORECASE)
                    and isno) and not re.findall(PETS_TEMPLATE, user_uttr["text"])
    logger.info(f"ask_about_playing_request, users_pet {users_pet} found_pet {found_pet} user_has_not {user_has_not} "
                f"isno {isno} asked_play {asked_play}")
    if not user_has_not and not asked_play \
            and (found_pet or users_pet_name or users_pet or (bot_asked_pet and (isyes or user_has))) \
            and not found_play:
        flag = True
    logger.info(f"ask_about_playing_request={flag}")
    return flag


def ask_like_request(ngrams, vars):
    flag = False
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    user_uttr = state_utils.get_last_human_utterance(vars)
    shared_memory = state_utils.get_shared_memory(vars)
    found_pet = re.findall(PETS_TEMPLATE, user_uttr["text"])
    delete_pet(vars)
    users_pet = shared_memory.get("users_pet", "")
    users_pet_name = shared_memory.get("users_pet_name", "")
    isyes = is_yes(state_utils.get_last_human_utterance(vars))
    user_has = re.findall(r"i (have|had)", user_uttr["text"])
    bot_asked_pet = re.findall(r"do you have a (cat|dog|rat|fish|parrot|hamster)", bot_uttr["text"], re.IGNORECASE)
    asked_like = shared_memory.get("asked_like", False)
    found_like = re.findall("(like|love)", user_uttr["text"])
    isno = is_no(state_utils.get_last_human_utterance(vars))
    user_has_not = (re.findall("do you have a (cat|dog|rat|fish|parrot|hamster)", bot_uttr["text"], re.IGNORECASE)
                    and isno) and not re.findall(PETS_TEMPLATE, user_uttr["text"])
    logger.info(f"ask_like_request, users_pet {users_pet} found_pet {found_pet} user_has_not {user_has_not} "
                f"isno {isno} asked_like {asked_like}")
    if not user_has_not and not asked_like \
            and (found_pet or users_pet_name or users_pet or (bot_asked_pet and (isyes or user_has))) \
            and not found_like:
        flag = True
    logger.info(f"ask_like_request={flag}")
    return flag


def ask_more_info_request(ngrams, vars):
    flag = False
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    user_uttr = state_utils.get_last_human_utterance(vars)
    shared_memory = state_utils.get_shared_memory(vars)
    found_pet = re.findall(PETS_TEMPLATE, user_uttr["text"])
    delete_pet(vars)
    users_pet = shared_memory.get("users_pet", "")
    isyes = is_yes(state_utils.get_last_human_utterance(vars))
    user_has = re.findall(r"i (have|had)", user_uttr["text"])
    bot_asked_pet = re.findall(r"do you have a (cat|dog|rat|fish|parrot|hamster)", bot_uttr["text"], re.IGNORECASE)
    asked_more_info = shared_memory.get("asked_more_info", False)
    isno = is_no(state_utils.get_last_human_utterance(vars))
    user_has_not = (re.findall("do you have a (cat|dog|rat|fish|parrot|hamster)", bot_uttr["text"], re.IGNORECASE)
                    and isno) and not re.findall(PETS_TEMPLATE, user_uttr["text"])
    if not user_has_not and not asked_more_info \
            and (found_pet or users_pet or (bot_asked_pet and (isyes or user_has))) and "feed" not in user_uttr["text"]:
        flag = True
    logger.info(f"ask_about_feeding_request={flag}")
    return flag


def to_animals_flow_request(ngrams, vars):
    flag = True
    logger.info(f"to_animals_flow_request={flag}")
    return flag


def what_pets_response(vars):
    response = "What pets do you have?"
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars, continue_flag=common_constants.MUST_CONTINUE)
    return response


def ask_about_dog_cat_response(vars):
    response = ""
    found_users_pet = retrieve_and_save(vars)
    if found_users_pet in {"cat", "dog"}:
        pet_phrase = choose_pet_phrase(vars, found_users_pet)
        response = f"{pet_phrase} Do you have a {found_users_pet}?".strip()
    if response:
        state_utils.set_confidence(vars, confidence=CONF_1)
        state_utils.set_can_continue(vars, continue_flag=common_constants.MUST_CONTINUE)
    else:
        state_utils.set_confidence(vars, confidence=0.0)
        state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_NOT_CONTINUE)
    return response


def ask_about_name_response(vars):
    retrieve_and_save(vars)
    extract_breed(vars)
    response = make_utt_with_ack(vars, UserPetsState.SYS_ASK_ABOUT_NAME)
    state_utils.save_to_shared_memory(vars, start=True)
    state_utils.save_to_shared_memory(vars, asked_name=True)
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars, continue_flag=common_constants.MUST_CONTINUE)
    return response


def suggest_pet_response(vars):
    phrases = [phrase for pet_phrases in CATS_DOGS_PHRASES.values() for phrase in pet_phrases]
    response = random.choice(phrases)
    state_utils.save_to_shared_memory(vars, start=True)
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars, continue_flag=common_constants.MUST_CONTINUE)
    return response


def ask_about_breed_response(vars):
    retrieve_and_save(vars)
    extract_breed(vars)
    retrieve_and_save_name(vars)
    response = make_utt_with_ack(vars, UserPetsState.SYS_WHAT_BREED)
    state_utils.save_to_shared_memory(vars, start=True)
    state_utils.save_to_shared_memory(vars, asked_breed=True)
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    return response


def ask_about_playing_response(vars):
    retrieve_and_save(vars)
    extract_breed(vars)
    retrieve_and_save_name(vars)
    response = make_utt_with_ack(vars, UserPetsState.SYS_PLAY_WITH_PET)
    state_utils.save_to_shared_memory(vars, start=True)
    state_utils.save_to_shared_memory(vars, asked_play=True)
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    return response


def ask_like_response(vars):
    retrieve_and_save(vars)
    extract_breed(vars)
    retrieve_and_save_name(vars)
    response = make_utt_with_ack(vars, UserPetsState.SYS_LIKE_PET)
    state_utils.save_to_shared_memory(vars, start=True)
    state_utils.save_to_shared_memory(vars, asked_like=True)
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    return response


def ask_more_info_response(vars):
    retrieve_and_save(vars)
    retrieve_and_save_name(vars)
    response = make_utt_with_ack(vars, UserPetsState.SYS_ASK_MORE_INFO)
    state_utils.save_to_shared_memory(vars, start=True)
    state_utils.save_to_shared_memory(vars, asked_more_info=True)
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
        UserPetsState.SYS_ERR: stop_animals_request,
        UserPetsState.SYS_WHAT_PETS: what_pets_request,
        UserPetsState.SYS_IS_DOG_CAT: is_dog_cat_request,
        UserPetsState.SYS_NOT_HAVE: not_have_pets_request,
        UserPetsState.SYS_ASK_ABOUT_NAME: ask_about_name_request,
        UserPetsState.SYS_WHAT_BREED: ask_about_breed_request,
        UserPetsState.SYS_PLAY_WITH_PET: ask_about_playing_request,
        UserPetsState.SYS_LIKE_PET: ask_like_request,
        (scopes.ANIMALS, AnimalsState.USR_START): to_animals_flow_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    UserPetsState.USR_WHAT_PETS,
    {
        UserPetsState.SYS_ERR: stop_animals_request,
        UserPetsState.SYS_ASK_ABOUT_NAME: ask_about_name_request,
        UserPetsState.SYS_WHAT_BREED: ask_about_breed_request,
        UserPetsState.SYS_PLAY_WITH_PET: ask_about_playing_request,
        UserPetsState.SYS_LIKE_PET: ask_like_request,
        (scopes.ANIMALS, AnimalsState.USR_START): to_animals_flow_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    UserPetsState.USR_ASK_ABOUT_DOG_CAT,
    {
        UserPetsState.SYS_ERR: stop_animals_request,
        UserPetsState.SYS_ASK_ABOUT_NAME: ask_about_name_request,
        UserPetsState.SYS_WHAT_BREED: ask_about_breed_request,
        UserPetsState.SYS_PLAY_WITH_PET: ask_about_playing_request,
        UserPetsState.SYS_LIKE_PET: ask_like_request,
        UserPetsState.SYS_ASK_MORE_INFO: ask_more_info_request,
        (scopes.ANIMALS, AnimalsState.USR_START): to_animals_flow_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    UserPetsState.USR_ASK_ABOUT_NAME,
    {
        UserPetsState.SYS_ERR: stop_animals_request,
        UserPetsState.SYS_WHAT_BREED: ask_about_breed_request,
        UserPetsState.SYS_PLAY_WITH_PET: ask_about_playing_request,
        UserPetsState.SYS_LIKE_PET: ask_like_request,
        UserPetsState.SYS_ASK_MORE_INFO: ask_more_info_request,
        (scopes.ANIMALS, AnimalsState.USR_START): to_animals_flow_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    UserPetsState.USR_NOT_HAVE,
    {
        UserPetsState.SYS_ERR: stop_animals_request,
        (scopes.ANIMALS, AnimalsState.USR_START): to_animals_flow_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    UserPetsState.USR_WHAT_BREED,
    {
        UserPetsState.SYS_ERR: stop_animals_request,
        UserPetsState.SYS_ASK_ABOUT_NAME: ask_about_name_request,
        UserPetsState.SYS_PLAY_WITH_PET: ask_about_playing_request,
        UserPetsState.SYS_LIKE_PET: ask_like_request,
        UserPetsState.SYS_ASK_MORE_INFO: ask_more_info_request,
        (scopes.ANIMALS, AnimalsState.USR_START): to_animals_flow_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    UserPetsState.USR_PLAY_WITH_PET,
    {
        UserPetsState.SYS_ERR: stop_animals_request,
        UserPetsState.SYS_ASK_ABOUT_NAME: ask_about_name_request,
        UserPetsState.SYS_LIKE_PET: ask_like_request,
        UserPetsState.SYS_ASK_MORE_INFO: ask_more_info_request,
        (scopes.ANIMALS, AnimalsState.USR_START): to_animals_flow_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    UserPetsState.USR_LIKE_PET,
    {
        UserPetsState.SYS_ERR: stop_animals_request,
        UserPetsState.SYS_ASK_ABOUT_NAME: ask_about_name_request,
        UserPetsState.SYS_PLAY_WITH_PET: ask_about_playing_request,
        UserPetsState.SYS_ASK_MORE_INFO: ask_more_info_request,
        (scopes.ANIMALS, AnimalsState.USR_START): to_animals_flow_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    UserPetsState.USR_ASK_MORE_INFO,
    {
        UserPetsState.SYS_ERR: stop_animals_request,
        UserPetsState.SYS_WHAT_BREED: ask_about_breed_request,
        UserPetsState.SYS_PLAY_WITH_PET: ask_about_playing_request,
        UserPetsState.SYS_LIKE_PET: ask_like_request,
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
simplified_dialog_flow.add_system_transition(UserPetsState.SYS_PLAY_WITH_PET, UserPetsState.USR_PLAY_WITH_PET,
                                             ask_about_playing_response, )
simplified_dialog_flow.add_system_transition(UserPetsState.SYS_LIKE_PET, UserPetsState.USR_LIKE_PET,
                                             ask_like_response, )
simplified_dialog_flow.add_system_transition(UserPetsState.SYS_ASK_MORE_INFO, UserPetsState.USR_ASK_MORE_INFO,
                                             ask_more_info_response, )

simplified_dialog_flow.set_error_successor(UserPetsState.USR_START, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.SYS_WHAT_PETS, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.SYS_IS_DOG_CAT, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.USR_WHAT_PETS, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.SYS_ASK_ABOUT_NAME, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.USR_ASK_ABOUT_NAME, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.SYS_NOT_HAVE, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.USR_NOT_HAVE, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.SYS_WHAT_BREED, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.USR_WHAT_BREED, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.SYS_PLAY_WITH_PET, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.USR_PLAY_WITH_PET, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.SYS_LIKE_PET, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.USR_LIKE_PET, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.SYS_ASK_MORE_INFO, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.USR_ASK_MORE_INFO, UserPetsState.SYS_ERR)

simplified_dialog_flow.add_system_transition(
    UserPetsState.SYS_ERR,
    (scopes.MAIN, scopes.State.USR_ROOT),
    error_response,
)

dialogflow = simplified_dialog_flow.get_dialogflow()
