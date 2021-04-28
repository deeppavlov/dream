import logging
import os
import re
import en_core_web_sm
import nltk
import sentry_sdk

from deeppavlov import build_model

import common.constants as common_constants
import common.dialogflow_framework.stdm.dialogflow_extention as dialogflow_extention
import common.dialogflow_framework.utils.state as state_utils
from common.universal_templates import COMPILE_NOT_WANT_TO_TALK_ABOUT_IT
from common.utils import is_no
from common.wiki_skill import used_types_dict, used_types, used_substr, prohibited_topics, prohibited_types
from common.wiki_skill import choose_title, find_all_titles, find_paragraph

import dialogflows.scopes as scopes
from dialogflows.flows.wiki_states import State as WikiState

sentry_sdk.init(os.getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

nlp = en_core_web_sm.load()

config_name = os.getenv("CONFIG")

page_extractor = build_model(config_name, download=True)

titles_by_type = {}
for elem in used_types_dict:
    types = elem.get("types", [])
    titles = elem["titles"]
    for tp in types:
        titles_by_type[tp] = titles

titles_by_entity_substr = {}
for elem in used_types_dict:
    entity_substrings = elem.get("entity_substr", [])
    titles = elem["titles"]
    for substr in entity_substrings:
        titles_by_entity_substr[substr] = titles

CONF_1 = 1.0
CONF_2 = 0.98
CONF_3 = 0.95
CONF_4 = 0.0

found_pages_dict = {}


def find_entity(vars):
    found_entity_substr = ""
    found_entity_types = []
    annotations = state_utils.get_last_human_utterance(vars)["annotations"]
    wp_output = annotations.get("wiki_parser", {})
    if isinstance(wp_output, dict):
        entities_info = wp_output.get("entities_info", {})
        logger.info(f"used_types {used_types}")
        logger.info(f"entities_info {entities_info}")
        for entity, triplets in entities_info.items():
            types = triplets.get("types", []) + triplets.get("instance of", []) + triplets.get("subclass of", [])
            type_ids = [elem for elem, label in types]
            inters = set(type_ids).intersection(used_types)
            in_not_used_types = set(type_ids).intersection(prohibited_types)
            in_not_used_substr = entity in prohibited_topics
            match_substr = entity in used_substr
            if (inters or match_substr) and not in_not_used_types and not in_not_used_substr:
                found_entity_types = inters
                found_entity_substr = entity
                break
    logger.info(f"find_entity, substr {found_entity_substr} types {found_entity_types}")
    return found_entity_substr, found_entity_types


def get_page_title(vars, entity_substr):
    found_page = ""
    annotations = state_utils.get_last_human_utterance(vars)["annotations"]
    el = annotations.get("entity_linking", [])
    for entity in el:
        if isinstance(entity, dict) and entity["entity_substr"] == entity_substr:
            found_pages_titles = entity["entity_pages_titles"]
            if found_pages_titles:
                found_page = found_pages_titles[0]
    logger.info(f"found_page {found_page}")
    return found_page


def get_page_content(page_title):
    page_content = {}
    try:
        if page_title:
            res = page_extractor([[page_title]])
            if res and res[0]:
                page_content = res[0][0]
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)

    return page_content


def tell_fact_request(ngrams, vars):
    flag = False
    shared_memory = state_utils.get_shared_memory(vars)
    user_uttr = state_utils.get_last_human_utterance(vars)
    started = shared_memory.get("start", False)
    curr_page = shared_memory.get("curr_page", "")
    found_entity_substr = shared_memory.get("found_entity_substr", "")
    prev_title = shared_memory.get("prev_title", "")
    used_titles = shared_memory.get("used_titles", [])
    found_entity_types = shared_memory.get("found_entity_types", [])
    if curr_page:
        page_content = get_page_content(curr_page)
    else:
        found_entity_substr, found_entity_types = find_entity(vars)
        curr_page = get_page_title(vars, found_entity_substr)
        page_content = get_page_content(curr_page)
        logger.info(f"request, found_entity_substr {found_entity_substr} found_entity_types {found_entity_types}")
        logger.info(f"request, curr_page {curr_page}")

    all_titles = find_all_titles([], page_content)
    logger.info(f"request, all_titles {all_titles}")
    titles_we_use = []
    for tp in found_entity_types:
        titles_we_use += list(titles_by_type.get(tp, {}).keys())
    titles_we_use += list(titles_by_entity_substr.get(found_entity_substr, {}).keys())

    logger.info(f"request, titles_we_use {titles_we_use}")
    chosen_title, chosen_page_title = choose_title(vars, all_titles, titles_we_use, prev_title, used_titles)
    logger.info(f"request, chosen_title {chosen_title} chosen_page_title {chosen_page_title}")
    isno = is_no(state_utils.get_last_human_utterance(vars))
    not_want = re.findall(COMPILE_NOT_WANT_TO_TALK_ABOUT_IT, user_uttr["text"])

    if (chosen_title or (prev_title and not isno and not not_want)) and (found_entity_types or started):
        flag = True
    logger.info(f"tell_fact_request={flag}")
    return flag


def tell_fact_response(vars):
    shared_memory = state_utils.get_shared_memory(vars)
    found_entity_substr = shared_memory.get("found_entity_substr", "")
    curr_page = shared_memory.get("curr_page", "")
    prev_title = shared_memory.get("prev_title", "")
    used_titles = shared_memory.get("used_titles", [])
    found_entity_types = shared_memory.get("found_entity_types", [])
    if curr_page:
        page_content = get_page_content(curr_page)
    else:
        found_entity_substr, found_entity_types = find_entity(vars)
        curr_page = get_page_title(vars, found_entity_substr)
        page_content = get_page_content(curr_page)
        logger.info(f"response, found_entity_substr {found_entity_substr} found_entity_types {found_entity_types}")
        logger.info(f"response, curr_page {curr_page}")

    all_titles = find_all_titles([], page_content)
    logger.info(f"all_titles {all_titles}")
    titles_we_use = []
    titles_q = {}
    for tp in found_entity_types:
        tp_titles = titles_by_type.get(tp, {})
        titles_we_use += list(tp_titles.keys())
        titles_q = {**titles_q, **tp_titles}
    substr_titles = titles_by_entity_substr.get(found_entity_substr, {})
    titles_we_use += list(substr_titles.keys())
    titles_q = {**titles_q, **substr_titles}
    logger.info(f"titles_q {titles_q}")

    all_titles = find_all_titles([], page_content)
    chosen_title, chosen_page_title = choose_title(vars, all_titles, titles_we_use, prev_title, used_titles)
    logger.info(f"chosen_title {chosen_title}")
    question = ""
    if chosen_title:
        if chosen_title in titles_q and titles_q[chosen_title]:
            question = titles_q[chosen_title].format(found_entity_substr)
        else:
            question = f"Would you like to know about {chosen_title} of {found_entity_substr}?"
        used_titles.append(chosen_title)
        state_utils.save_to_shared_memory(vars, found_entity_substr=found_entity_substr)
        state_utils.save_to_shared_memory(vars, curr_page=curr_page)
        state_utils.save_to_shared_memory(vars, prev_title=chosen_title)
        state_utils.save_to_shared_memory(vars, used_titles=used_titles)
        state_utils.save_to_shared_memory(vars, found_entity_types=list(found_entity_types))
    else:
        state_utils.save_to_shared_memory(vars, found_entity_substr="")
        state_utils.save_to_shared_memory(vars, curr_page="")
        state_utils.save_to_shared_memory(vars, prev_title="")
        state_utils.save_to_shared_memory(vars, used_titles=[])
        state_utils.save_to_shared_memory(vars, found_entity_types=[])

    facts_str = ""
    if prev_title:
        paragraph = ""
        paragraphs = find_paragraph(page_content, prev_title)
        logger.info(f"paragraphs {paragraphs}")
        if paragraphs:
            paragraph = paragraphs[0]
        sentences = nltk.sent_tokenize(paragraph)
        sentences_list = []
        cur_len = 0
        max_len = 50
        for sentence in sentences:
            words = nltk.word_tokenize(sentence)
            if cur_len + len(words) < max_len:
                sentences_list.append(sentence)
                cur_len += len(words)
        if sentences_list:
            facts_str = " ".join(sentences_list)
        cur_len = 0
        if sentences and not sentences_list:
            sentence = sentences[0]
            sentence_parts = sentence.split(", ")
            for part in sentence_parts:
                words = nltk.word_tokenize(part)
                if cur_len + len(words) < max_len:
                    sentences_list.append(part)
                    cur_len += len(words)
                facts_str = ", ".join(sentences_list)
                if facts_str and not facts_str.endswith("."):
                    facts_str = f"{facts_str}."
    response = f"{facts_str} {question}"
    response = response.strip()

    started = shared_memory.get("start", False)
    if not started:
        state_utils.save_to_shared_memory(vars, start=True)
    if response:
        state_utils.set_confidence(vars, confidence=CONF_1)
    else:
        state_utils.set_confidence(vars, confidence=CONF_4)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    return response


def error_response(vars):
    state_utils.save_to_shared_memory(vars, start=False)
    state_utils.save_to_shared_memory(vars, found_entity_substr="")
    state_utils.save_to_shared_memory(vars, curr_page="")
    state_utils.save_to_shared_memory(vars, prev_title="")
    state_utils.save_to_shared_memory(vars, used_titles=[])
    state_utils.save_to_shared_memory(vars, found_entity_types=[])
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_NOT_CONTINUE)
    state_utils.set_confidence(vars, 0)
    return ""


simplified_dialog_flow = dialogflow_extention.DFEasyFilling(WikiState.USR_START)

simplified_dialog_flow.add_user_serial_transitions(
    WikiState.USR_START,
    {
        WikiState.SYS_TELL_FACT: tell_fact_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    WikiState.USR_TELL_FACT,
    {
        WikiState.SYS_TELL_FACT: tell_fact_request,
    },
)

simplified_dialog_flow.add_system_transition(WikiState.SYS_TELL_FACT, WikiState.USR_TELL_FACT, tell_fact_response, )
simplified_dialog_flow.add_system_transition(WikiState.SYS_ERR, (scopes.MAIN, scopes.State.USR_ROOT), error_response, )

simplified_dialog_flow.set_error_successor(WikiState.USR_START, WikiState.SYS_ERR)
simplified_dialog_flow.set_error_successor(WikiState.SYS_TELL_FACT, WikiState.SYS_ERR)
simplified_dialog_flow.set_error_successor(WikiState.USR_TELL_FACT, WikiState.SYS_ERR)

dialogflow = simplified_dialog_flow.get_dialogflow()
