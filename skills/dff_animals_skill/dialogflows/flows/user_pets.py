import json
import logging
import random
import os
import re
import sentry_sdk

import common.constants as common_constants
from dff import dialogflow_extension
import common.dialogflow_framework.utils.state as state_utils
import common.dialogflow_framework.utils.condition as condition_utils
from common.utils import is_no, is_yes
import dialogflows.scopes as scopes
from dialogflows.flows.user_pets_states import State as UserPetsState
from dialogflows.flows.animals_states import State as AnimalsState
from dialogflows.flows.animals import make_my_pets_info
from common.animals import (
    PETS_TEMPLATE,
    CATS_DOGS_PHRASES,
    USER_PETS_Q,
    stop_about_animals,
    pet_games,
    breed_replace_dict,
)

sentry_sdk.init(os.getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)

CONF_1 = 1.0
CONF_2 = 0.99
CONF_3 = 0.95

breeds_dict = {}
CATS_DOGS = {"cat", "dog", "puppy", "kitten", "kitty", "cats", "dogs", "kitties", "kittens", "puppies"}

try:
    with open("/root/.deeppavlov/downloads/wikidata/breed_facts.json", "r") as fl:
        breeds_dict = json.load(fl)
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)


def extract_pet(utt):
    fnd = re.findall(r"(cat|dog|rat|fish|bird|parrot|hamster|puppy|kitty|kitten)", utt)
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
    found_pet = re.findall(
        "(don't|do not) have (a )?(cat|dog|rat|fish|bird|parrot|hamster|puppy|kitten|kitty)", user_text
    )
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
        found_pet_bot_uttr = re.findall(
            r"(do you have a )(cat|dog|rat|fish|bird|parrot|hamster|puppy|kitten|kitty)", bot_uttr, re.IGNORECASE
        )
        if found_users_pet:
            state_utils.save_to_shared_memory(vars, users_pet=found_users_pet)
        elif found_pet_bot_uttr and isyes:
            state_utils.save_to_shared_memory(vars, users_pet=found_pet_bot_uttr[0][1])
            found_users_pet = found_pet_bot_uttr[0][1]
    logger.info(
        f"retrieve_and_save, found_users_pet {found_users_pet} found_pet_bot_uttr {found_pet_bot_uttr}"
        f" isyes {isyes}"
    )
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

    if (
        found_name
        and not shared_memory.get("users_pet_name", "")
        and found_name not in {"black", "white", "grey", "brown", "yellow", "cat", "dog"}
        and found_name not in users_pet_breed
    ):
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
        nounphrases = annotations.get("cobot_entities", {}).get("entities", []) + annotations.get(
            "spacy_nounphrases", []
        )
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


def replace_pet(pet):
    if pet in {"dogs", "puppy", "puppies"}:
        return "dog"
    elif pet in {"cats", "kitty", "kitties", "kitten", "kittens"}:
        return "cat"
    else:
        return pet


def make_utt_with_ack(vars, prev_what_to_ask, what_to_ask):
    ack = ""
    statement = ""
    question = ""
    user_uttr = state_utils.get_last_human_utterance(vars)
    shared_memory = state_utils.get_shared_memory(vars)
    make_my_pets_info(vars)
    prev_state = condition_utils.get_last_state(vars)
    about_users_pet = str(prev_state).split(".")[-1] == "SYS_ASK_ABOUT_PET"
    isno = is_no(state_utils.get_last_human_utterance(vars))
    users_pet = shared_memory.get("users_pet", "")
    users_pet_name = shared_memory.get("users_pet_name", "")
    users_pet_breed = shared_memory.get("users_pet_breed", "")
    logger.info(
        f"make_utt_with_ack users_pet {users_pet} users_pet_name {users_pet_name} "
        f"users_pet_breed {users_pet_breed} {breeds_dict.get('users_pet_breed', '')} "
        f"about_users_pet {about_users_pet}"
    )
    my_pets_info = shared_memory.get("my_pets_info", {})
    if about_users_pet and prev_what_to_ask == "name" and users_pet_name:
        ack = "Very cool name! You have such an amusing mind!"
    if about_users_pet and prev_what_to_ask == "breed":
        if users_pet and users_pet_breed:
            breed_info = breeds_dict[users_pet_breed]
            facts = breed_info.get("facts", "")
            if not facts.endswith("."):
                facts = f"{facts}."
            if facts:
                ack = f"I know a lot about {users_pet} breeds. {facts}"
                #      + f"Would you like to know more about {users_pet_breed}?"
    if about_users_pet and prev_what_to_ask == "play" and not isno:
        ack = "Really, playing with a pet makes a lot of fun."
    if prev_what_to_ask == "videos" and not isno:
        if users_pet:
            ack = f"I would like to see videos with your {users_pet} if I could."
    if what_to_ask == "name":
        if users_pet in CATS_DOGS:
            repl_pet = replace_pet(users_pet)
            statement = choose_pet_phrase(vars, repl_pet)
        if users_pet:
            question = f"What is your {users_pet}'s name?"
        else:
            question = "What is your pet's name?"
    if what_to_ask == "breed":
        if users_pet in CATS_DOGS:
            repl_pet = replace_pet(users_pet)
            my_pet = my_pets_info[repl_pet]
            my_pet_breed = my_pet["breed"]
            statement = f"I have a {my_pet_breed} {users_pet}."
            question = f"What is your {users_pet}'s breed?"
    if what_to_ask == "play":
        if users_pet in CATS_DOGS:
            repl_pet = replace_pet(users_pet)
            games = " and ".join(pet_games[repl_pet])
            statement = f"I like to play with my {users_pet} different games, such as {games}."
        if users_pet:
            question = f"Do you play with your {users_pet}?"
    if what_to_ask == "like":
        statement = "There's an old saying that pets repay the love you give them ten-fold."
        if users_pet_name:
            question = f"Do you like {users_pet_name}?"
        elif users_pet:
            question = f"Do you like your {users_pet}?"
        else:
            question = "Do you like your pet?"
    if what_to_ask == "videos":
        statement = "I saw a lot of funny videos with pets on Youtube."
        question = "Did you shoot any videos with your pet?"
    if what_to_ask == "pandemic":
        statement = "Nowadays during pandemic we have to stay at home."
        question = "Does your pet help you to cheer up during pandemic?"
    if "bark" in user_uttr["text"]:
        ack = f"Woof-woof, bow-bow, ruff-ruff! {ack}"
    used_acks = shared_memory.get("used_acks", [])
    if ack and ack in used_acks:
        ack = ""
    else:
        used_acks.append(ack)
        state_utils.save_to_shared_memory(vars, used_acks=used_acks)
    response = f"{ack} {statement} {question}"
    response = response.replace("  ", " ").strip()
    return response


def stop_animals_request(ngrams, vars):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    shared_memory = state_utils.get_shared_memory(vars)
    if stop_about_animals(user_uttr, shared_memory):
        flag = True
    logger.info(f"stop_animals_request={flag}")
    return flag


def my_pets_request(ngrams, vars):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    have_pet = re.findall(r"(do|did) you have (a )?(dog|cat|puppy|kitty|kitten)s?", user_uttr["text"])
    tell_about_pet = re.findall(r"(tell|talk|hear)(.*)(your )(dog|cat|puppy|kitty|kitten)s?", user_uttr["text"])
    if have_pet or tell_about_pet:
        flag = True
    logger.info(f"my_pets_request={flag}")
    return flag


def what_pets_request(ngrams, vars):
    flag = False
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    user_uttr = state_utils.get_last_human_utterance(vars)
    isyes = is_yes(state_utils.get_last_human_utterance(vars))
    user_has = re.findall(r"i (have|had)", user_uttr["text"])
    mention_pet = re.findall(PETS_TEMPLATE, user_uttr["text"])
    asked_about_pets = "do you have pets" in bot_uttr["text"].lower()
    bot_asked_pet = re.findall(r"do you have a (cat|dog|rat|fish|bird|parrot|hamster)", bot_uttr["text"], re.IGNORECASE)
    logger.info(f"what_pets_request, {asked_about_pets}, {isyes}, {user_has}, {mention_pet}")
    my_pets = my_pets_request(ngrams, vars)
    if not my_pets and asked_about_pets and (isyes or user_has) and not mention_pet and not (bot_asked_pet and is_yes):
        flag = True
    logger.info(f"what_pets_request={flag}")
    return flag


def another_pet_request(ngrams, vars):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    shared_memory = state_utils.get_shared_memory(vars)
    users_pet = shared_memory.get("users_pet", "")
    another_pet = re.findall(r"my (cat|dog)", user_uttr["text"])
    my_pets = my_pets_request(ngrams, vars)
    if not my_pets and another_pet and users_pet and another_pet[0] != users_pet:
        flag = True
    logger.info(f"another_pet_request, users_pet {users_pet} another_pet {another_pet}")
    logger.info(f"another_pet_request={flag}")
    return flag


def ask_about_pet_request(ngrams, vars):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    isno = is_no(state_utils.get_last_human_utterance(vars))
    isyes = is_yes(state_utils.get_last_human_utterance(vars))
    user_has = re.findall(r"i (have|had)", user_uttr["text"])
    extract_breed(vars)
    delete_pet(vars)
    bot_asked_pet = re.findall(r"do you have a (cat|dog|rat|fish|bird|parrot|hamster)", bot_uttr["text"], re.IGNORECASE)
    user_has_not = (bot_asked_pet and isno) and not re.findall(PETS_TEMPLATE, user_uttr["text"])
    user_told_pet = re.findall("(cat|dog|rat|fish|bird|parrot|hamster)", user_uttr["text"]) and re.findall(
        r"(do you have pets|what pets do you have)", bot_uttr["text"], re.IGNORECASE
    )
    user_mentioned_pet = re.findall(
        r"my (cat|dog|rat|fish|bird|parrot|hamster|puppy|kitty|kitten)", user_uttr["text"], re.IGNORECASE
    )
    user_has_pet = re.findall(
        r"i (have |had )(a )?(cat|dog|rat|fish|bird|parrot|hamster|puppy|kitty|kitten)",
        user_uttr["text"],
        re.IGNORECASE,
    )
    shared_memory = state_utils.get_shared_memory(vars)
    found_pet = re.findall(PETS_TEMPLATE, user_uttr["text"])
    used_pets_q = shared_memory.get("used_pets_q", [])
    users_pet = shared_memory.get("users_pet", "")
    my_pets = my_pets_request(ngrams, vars)
    found_question = {}
    logger.info(
        f"ask_about_pet_request, my_pets {my_pets} user_has_not {user_has_not} users_pet {users_pet} "
        f"bot_asked_pet {bot_asked_pet} isyes {isyes} user_has {user_has} user_told_pet {user_told_pet} "
        f"user_mentioned_pet {user_mentioned_pet} user_has_pet {user_has_pet} found_pet {found_pet}"
    )
    if (
        not my_pets
        and not user_has_not
        and (
            users_pet or (bot_asked_pet and (isyes or user_has)) or user_told_pet or user_mentioned_pet or user_has_pet
        )
    ):
        for elem in USER_PETS_Q:
            if elem["what"] not in used_pets_q:
                found_question = elem
                found_attr = ""
                if found_question and found_question["attr"]:
                    curr_attr = found_question["attr"]
                    found_attr = shared_memory.get(curr_attr, "")
                found_keywords = False
                if found_question and found_question["keywords"]:
                    keywords = found_question["keywords"]
                    found_keywords = any([keyword in user_uttr["text"] for keyword in keywords])
                if not found_attr and not found_keywords:
                    flag = True
                if found_question.get("what", "") == "breed" and (
                    (users_pet and users_pet not in CATS_DOGS) or (found_pet and found_pet[0] not in CATS_DOGS)
                ):
                    flag = False
                logger.info(
                    f"ask_about_pet, what {found_question.get('what', '')} found_attr {found_attr} "
                    f"found_keywords {found_keywords}"
                )
            if flag:
                break
    logger.info(f"ask_about_pet_request={flag}")
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
    my_pets = my_pets_request(ngrams, vars)
    if not my_pets and asked_like and user_mention_pet and not user_has:
        flag = True
    logger.info(f"is_dog_cat_request={flag}")
    return flag


def to_animals_flow_request(ngrams, vars):
    flag = True
    logger.info(f"to_animals_flow_request={flag}")
    return flag


def what_pets_response(vars):
    response = "What pets do you have?"
    state_utils.save_to_shared_memory(vars, start=True)
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars, continue_flag=common_constants.MUST_CONTINUE)
    return response


def ask_about_dog_cat_response(vars):
    response = ""
    found_users_pet = retrieve_and_save(vars)
    if found_users_pet in CATS_DOGS:
        repl_pet = replace_pet(found_users_pet)
        pet_phrase = choose_pet_phrase(vars, repl_pet)
        response = f"{pet_phrase} Do you have a {found_users_pet}?".strip()
    state_utils.save_to_shared_memory(vars, start=True)
    if response:
        state_utils.set_confidence(vars, confidence=CONF_1)
        state_utils.set_can_continue(vars, continue_flag=common_constants.MUST_CONTINUE)
    else:
        state_utils.set_confidence(vars, confidence=0.0)
        state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_NOT_CONTINUE)
    return response


def another_pet_response(vars):
    user_uttr = state_utils.get_last_human_utterance(vars)
    users_pet = re.findall(r"my (cat|dog)", user_uttr["text"])
    if users_pet:
        response = f"Very interesting! Could you tell more about your {users_pet[0]}?"
        state_utils.set_confidence(vars, confidence=CONF_1)
        state_utils.set_can_continue(vars, continue_flag=common_constants.MUST_CONTINUE)
    else:
        response = "Very interesting! Could you tell more about your pet?"
        state_utils.set_confidence(vars, confidence=CONF_2)
        state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    state_utils.save_to_shared_memory(vars, start=True)
    return response


def ask_about_pet_response(vars):
    retrieve_and_save(vars)
    extract_breed(vars)
    shared_memory = state_utils.get_shared_memory(vars)
    user_uttr = state_utils.get_last_human_utterance(vars)
    found_pet = re.findall(PETS_TEMPLATE, user_uttr["text"])
    users_pet = shared_memory.get("users_pet", "")
    used_pets_q = shared_memory.get("used_pets_q", [])
    found_question = {}
    flag = False
    for elem in USER_PETS_Q:
        if elem["what"] not in used_pets_q:
            found_question = elem
            found_attr = ""
            if found_question and found_question["attr"]:
                curr_attr = found_question["attr"]
                found_attr = shared_memory.get(curr_attr, "")
            found_keywords = False
            if found_question and found_question["keywords"]:
                keywords = found_question["keywords"]
                found_keywords = any([keyword in user_uttr["text"] for keyword in keywords])
            if not found_attr and not found_keywords:
                flag = True
            if (
                found_question.get("what", "") == "breed"
                and (users_pet and users_pet not in CATS_DOGS)
                or (found_pet and found_pet[0] not in CATS_DOGS)
            ):
                flag = False
        if flag:
            break
    what_to_ask = found_question.get("what", "")
    if what_to_ask != "name":
        retrieve_and_save_name(vars)
    prev_what_to_ask = ""
    if used_pets_q:
        prev_what_to_ask = used_pets_q[-1]
    response = make_utt_with_ack(vars, prev_what_to_ask, what_to_ask)
    if what_to_ask != "more_info":
        used_pets_q.append(what_to_ask)
    state_utils.save_to_shared_memory(vars, used_pets_q=used_pets_q)
    state_utils.save_to_shared_memory(vars, start=True)
    state_utils.set_confidence(vars, confidence=CONF_2)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    return response


def suggest_pet_response(vars):
    phrases = [phrase for pet_phrases in CATS_DOGS_PHRASES.values() for phrase in pet_phrases]
    response = random.choice(phrases)
    state_utils.save_to_shared_memory(vars, start=True)
    state_utils.set_confidence(vars, confidence=CONF_2)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    return response


def error_response(vars):
    state_utils.set_confidence(vars, 0)
    return ""


simplified_dialog_flow = dialogflow_extension.DFEasyFilling(UserPetsState.USR_START)

simplified_dialog_flow.add_user_serial_transitions(
    UserPetsState.USR_START,
    {
        UserPetsState.SYS_ERR: stop_animals_request,
        UserPetsState.SYS_WHAT_PETS: what_pets_request,
        UserPetsState.SYS_IS_DOG_CAT: is_dog_cat_request,
        UserPetsState.SYS_ANOTHER_PET: another_pet_request,
        UserPetsState.SYS_NOT_HAVE: not_have_pets_request,
        UserPetsState.SYS_ASK_ABOUT_PET: ask_about_pet_request,
        (scopes.ANIMALS, AnimalsState.USR_START): to_animals_flow_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    UserPetsState.USR_WHAT_PETS,
    {
        UserPetsState.SYS_ERR: stop_animals_request,
        UserPetsState.SYS_ASK_ABOUT_PET: ask_about_pet_request,
        UserPetsState.SYS_ANOTHER_PET: another_pet_request,
        (scopes.ANIMALS, AnimalsState.USR_START): to_animals_flow_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    UserPetsState.USR_ASK_ABOUT_DOG_CAT,
    {
        UserPetsState.SYS_ERR: stop_animals_request,
        UserPetsState.SYS_ASK_ABOUT_PET: ask_about_pet_request,
        UserPetsState.SYS_ANOTHER_PET: another_pet_request,
        (scopes.ANIMALS, AnimalsState.USR_START): to_animals_flow_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    UserPetsState.USR_ASK_ABOUT_PET,
    {
        UserPetsState.SYS_ERR: stop_animals_request,
        UserPetsState.SYS_ASK_ABOUT_PET: ask_about_pet_request,
        UserPetsState.SYS_ANOTHER_PET: another_pet_request,
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

simplified_dialog_flow.add_system_transition(
    UserPetsState.SYS_WHAT_PETS,
    UserPetsState.USR_WHAT_PETS,
    what_pets_response,
)
simplified_dialog_flow.add_system_transition(
    UserPetsState.SYS_IS_DOG_CAT,
    UserPetsState.USR_ASK_ABOUT_DOG_CAT,
    ask_about_dog_cat_response,
)
simplified_dialog_flow.add_system_transition(
    UserPetsState.SYS_ANOTHER_PET,
    UserPetsState.USR_ANOTHER_PET,
    another_pet_response,
)
simplified_dialog_flow.add_system_transition(
    UserPetsState.SYS_NOT_HAVE,
    UserPetsState.USR_NOT_HAVE,
    suggest_pet_response,
)
simplified_dialog_flow.add_system_transition(
    UserPetsState.SYS_ASK_ABOUT_PET,
    UserPetsState.USR_ASK_ABOUT_PET,
    ask_about_pet_response,
)

simplified_dialog_flow.set_error_successor(UserPetsState.USR_START, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.SYS_WHAT_PETS, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.SYS_IS_DOG_CAT, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.USR_WHAT_PETS, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.SYS_ASK_ABOUT_PET, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.USR_ASK_ABOUT_PET, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.SYS_NOT_HAVE, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.USR_NOT_HAVE, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.SYS_ANOTHER_PET, UserPetsState.SYS_ERR)
simplified_dialog_flow.set_error_successor(UserPetsState.USR_ANOTHER_PET, UserPetsState.SYS_ERR)

simplified_dialog_flow.add_system_transition(
    UserPetsState.SYS_ERR,
    (scopes.MAIN, scopes.State.USR_ROOT),
    error_response,
)

dialogflow = simplified_dialog_flow.get_dialogflow()
