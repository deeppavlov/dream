import logging
import os
import re
import en_core_web_sm
import inflect
import sentry_sdk

import common.constants as common_constants
import common.dialogflow_framework.stdm.dialogflow_extention as dialogflow_extention
import common.dialogflow_framework.utils.state as state_utils
from common.utils import is_no
import dialogflows.scopes as scopes
from dialogflows.flows.wild_animals_states import State as WAS
from dialogflows.flows.animals_states import State as AnimalsState
from common.animals import PETS_TEMPLATE, stop_about_animals
from common.wiki_skill import if_linked_to_wiki_skill

sentry_sdk.init(os.getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

nlp = en_core_web_sm.load()
p = inflect.engine()

CONF_1 = 1.0
CONF_2 = 0.99
CONF_3 = 0.95


def plural_nouns(text):
    plural_text = text
    try:
        processed_text = nlp(text)
        processed_tokens = []
        for token in processed_text:
            if token.tag_ == "NNP":
                processed_tokens.append(p.plural_noun(token.text))
            else:
                processed_tokens.append(token.text)
        plural_text = " ".join(processed_tokens)
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
    return plural_text


def activate_after_wiki_skill(vars):
    flag = False
    cross_link = state_utils.get_cross_link(vars, service_name="dff_animals_skill")
    from_skill = cross_link.get("from_service", "")
    isno = is_no(state_utils.get_last_human_utterance(vars))
    if from_skill == "dff_wiki_skill" and isno:
        flag = True
    logger.info(f"activate_after_wiki_skill {cross_link}")
    return flag


def stop_animals_request(ngrams, vars):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    shared_memory = state_utils.get_shared_memory(vars)
    stop_about_animals(user_uttr, shared_memory)
    if stop_about_animals(user_uttr, shared_memory):
        flag = True
    logger.info(f"stop_animals_request={flag}")
    return flag


def ask_about_zoo_request(ngrams, vars):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)["text"]
    bot_uttr = state_utils.get_last_bot_utterance(vars)["text"]
    shared_memory = state_utils.get_shared_memory(vars)
    user_why_phrases = ["cause", "they", "i like"]
    if "why do you like" in bot_uttr.lower() and all([phrase not in user_uttr for phrase in user_why_phrases]):
        flag = False
    if not shared_memory.get("ask_about_zoo", False) and shared_memory.get("why_do_you_like", False):
        flag = True
    logger.info(f"sys_ask_about_zoo_request={flag}")
    return flag


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


def why_do_you_like_request(ngrams, vars):
    flag = False
    text = state_utils.get_last_human_utterance(vars)["text"]
    annotations = state_utils.get_last_human_utterance(vars)["annotations"]
    conceptnet = annotations.get("conceptnet", {})
    found_animal = ""
    for elem, triplets in conceptnet.items():
        if "SymbolOf" in triplets:
            objects = triplets["SymbolOf"]
            if "animal" in objects:
                found_animal = elem
    wp_output = annotations.get("wiki_parser", {})
    if isinstance(wp_output, dict):
        entities_info = wp_output.get("entities_info", {})
        for entity, triplets in entities_info.items():
            types = triplets.get("types", []) + triplets.get("instance of", []) + triplets.get("subclass of", []) + \
                triplets.get("types_2hop", [])
            type_ids = [elem for elem, label in types]
            inters = set(type_ids).intersection({"Q55983715", "Q16521"})
            if inters:
                found_animal = entity
                break
    isno = is_no(state_utils.get_last_human_utterance(vars))
    shared_memory = state_utils.get_shared_memory(vars)
    used_why = shared_memory.get("why_do_you_like", False)
    found_pet = re.findall(PETS_TEMPLATE, text)
    found_bird = re.findall(r"(\bbird\b|\bbirds\b)", text)
    logger.info(f"why_do_you_like_request, found_animal {found_animal}")
    if (found_animal or found_bird) and not found_pet and not used_why and not isno \
            and not if_linked_to_wiki_skill(annotations, "dff_animals_skill"):
        flag = True
    if activate_after_wiki_skill(vars):
        flag = True
    logger.info(f"why_do_you_like_request={flag}")
    return flag


def ask_about_zoo_response(vars):
    i_went_zoo = "Last weekend I went to the zoo with my family. We had a great day."
    question_zoo = "When have you been to the zoo last time?"
    response = " ".join([i_went_zoo, question_zoo])
    state_utils.save_to_shared_memory(vars, ask_about_zoo=True)
    state_utils.set_confidence(vars, confidence=CONF_3)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    logger.info(f"ask_about_zoo_response: {response}")
    return response


def ask_more_details_response(vars):
    response = "What is your impression? What did you like most?"
    state_utils.set_confidence(vars, confidence=CONF_2)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    logger.info(f"ask_more_details_response: {response}")
    return response


def suggest_visiting_response(vars):
    response = "A day at the zoo also encourages a healthy lifestyle while bringing family and friends together. " + \
               "It is the perfect day trip destination for any season!"
    state_utils.set_confidence(vars, confidence=CONF_2)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    logger.info(f"suggest_visiting_response: {response}")
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
    wp_output = annotations.get("wiki_parser", {})
    if isinstance(wp_output, dict):
        entities_info = wp_output.get("entities_info", {})
        for entity, triplets in entities_info.items():
            types = triplets.get("types", []) + triplets.get("instance of", []) + triplets.get("subclass of", [])
            type_ids = [elem for elem, label in types]
            inters = set(type_ids).intersection({"Q55983715", "Q16521"})
            if inters:
                found_animal = entity
                found_animal = plural_nouns(found_animal)
                break
    if found_animal:
        response = f"Cool! Why do you like {found_animal}?"
    else:
        response = f"Cool! Why do you like them?"
    state_utils.save_to_shared_memory(vars, is_wild=True)
    state_utils.save_to_shared_memory(vars, why_do_you_like=True)
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars, continue_flag=common_constants.MUST_CONTINUE)
    logger.info(f"why_do_you_like_response: {response}")
    return response


def to_animals_flow_request(ngrams, vars):
    flag = True
    logger.info(f"to_animals_flow_request={flag}")
    return flag


def error_response(vars):
    state_utils.set_confidence(vars, 0)
    return ""


simplified_dialog_flow = dialogflow_extention.DFEasyFilling(WAS.USR_START)

simplified_dialog_flow.add_user_serial_transitions(
    WAS.USR_START,
    {
        WAS.SYS_WHY_DO_YOU_LIKE: why_do_you_like_request,
        (scopes.ANIMALS, AnimalsState.USR_START): to_animals_flow_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    WAS.USR_WHY_DO_YOU_LIKE,
    {
        WAS.SYS_ASK_ABOUT_ZOO: ask_about_zoo_request,
        (scopes.ANIMALS, AnimalsState.USR_START): to_animals_flow_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    WAS.USR_ASK_ABOUT_ZOO,
    {
        WAS.SYS_USER_HAS_BEEN: user_has_been_request,
        WAS.SYS_USER_HAS_NOT_BEEN: user_has_not_been_request,
        (scopes.ANIMALS, AnimalsState.USR_START): to_animals_flow_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    WAS.USR_ASK_MORE_DETAILS,
    {
        (scopes.ANIMALS, AnimalsState.USR_START): to_animals_flow_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    WAS.USR_SUGGEST_VISITING,
    {
        (scopes.ANIMALS, AnimalsState.USR_START): to_animals_flow_request,
    },
)

simplified_dialog_flow.add_system_transition(WAS.SYS_WHY_DO_YOU_LIKE, WAS.USR_WHY_DO_YOU_LIKE,
                                             why_do_you_like_response, )
simplified_dialog_flow.add_system_transition(WAS.SYS_ASK_ABOUT_ZOO, WAS.USR_ASK_ABOUT_ZOO, ask_about_zoo_response, )
simplified_dialog_flow.add_system_transition(WAS.SYS_USER_HAS_BEEN, WAS.USR_ASK_MORE_DETAILS,
                                             ask_more_details_response, )
simplified_dialog_flow.add_system_transition(WAS.SYS_USER_HAS_NOT_BEEN, WAS.USR_SUGGEST_VISITING,
                                             suggest_visiting_response, )
simplified_dialog_flow.add_system_transition(WAS.SYS_ERR, (scopes.MAIN, scopes.State.USR_ROOT), error_response, )

simplified_dialog_flow.set_error_successor(WAS.USR_START, WAS.SYS_ERR)
simplified_dialog_flow.set_error_successor(WAS.SYS_WHY_DO_YOU_LIKE, WAS.SYS_ERR)
simplified_dialog_flow.set_error_successor(WAS.USR_WHY_DO_YOU_LIKE, WAS.SYS_ERR)
simplified_dialog_flow.set_error_successor(WAS.SYS_ASK_ABOUT_ZOO, WAS.SYS_ERR)
simplified_dialog_flow.set_error_successor(WAS.USR_ASK_ABOUT_ZOO, WAS.SYS_ERR)
simplified_dialog_flow.set_error_successor(WAS.SYS_USER_HAS_BEEN, WAS.SYS_ERR)
simplified_dialog_flow.set_error_successor(WAS.SYS_USER_HAS_NOT_BEEN, WAS.SYS_ERR)
simplified_dialog_flow.set_error_successor(WAS.USR_ASK_MORE_DETAILS, WAS.SYS_ERR)
simplified_dialog_flow.set_error_successor(WAS.USR_SUGGEST_VISITING, WAS.SYS_ERR)

dialogflow = simplified_dialog_flow.get_dialogflow()
