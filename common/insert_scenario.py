import logging
import os
import random
import re
import nltk
import requests
import sentry_sdk
import common.constants as common_constants
import common.dialogflow_framework.utils.state as state_utils
from common.universal_templates import if_chat_about_particular_topic

from common.wiki_skill import (
    check_condition,
    find_entity_by_types,
    check_nounphr,
    find_page_title,
    find_paragraph,
    delete_hyperlinks,
    find_all_titles,
    used_types_dict,
    NEWS_MORE,
    WIKI_BADLIST,
    QUESTION_TEMPLATES,
    QUESTION_TEMPLATES_SHORT,
    CONF_DICT,
)
from common.universal_templates import CONTINUE_PATTERN
from common.utils import is_no, is_yes

sentry_sdk.init(os.getenv("SENTRY_DSN"))
logger = logging.getLogger(__name__)
WIKI_FACTS_URL = os.getenv("WIKI_FACTS_URL")

memory = {}


titles_by_type = {}
for elem in used_types_dict:
    types = elem.get("types", [])
    titles = elem["titles"]
    for tp in types:
        titles_by_type[tp] = titles

titles_by_entity_substr = {}
page_titles_by_entity_substr = {}
for elem in used_types_dict:
    entity_substrings = elem.get("entity_substr", [])
    titles = elem["titles"]
    page_title = elem.get("page_title", "")
    for substr in entity_substrings:
        titles_by_entity_substr[substr] = titles
        if page_title:
            page_titles_by_entity_substr[substr] = page_title

questions_by_entity_substr = {}
for elem in used_types_dict:
    entity_substrings = elem.get("entity_substr", [])
    question = elem.get("intro_question", "")
    if question:
        for substr in entity_substrings:
            questions_by_entity_substr[substr] = question

wikihowq_by_substr = {}
for elem in used_types_dict:
    entity_substrings = elem.get("entity_substr", [])
    wikihow_info = elem.get("wikihow_info", {})
    if wikihow_info:
        for substr in entity_substrings:
            wikihowq_by_substr[substr] = wikihow_info


def get_page_content(page_title, cache_page_dict=None):
    page_content = {}
    main_pages = {}
    try:
        if page_title:
            if cache_page_dict and page_title in cache_page_dict:
                page_content = cache_page_dict[page_title]["page_content"]
                main_pages = cache_page_dict[page_title]["main_pages"]
            else:
                res = requests.post(WIKI_FACTS_URL, json={"wikipedia_titles": [[page_title]]}, timeout=1.0).json()
                if res and res[0]["main_pages"] and res[0]["wikipedia_content"]:
                    page_content = res[0]["wikipedia_content"][0]
                    main_pages = res[0]["main_pages"][0]
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)

    return page_content, main_pages


def get_wikihow_content(page_title):
    page_content = {}
    try:
        if page_title:
            res = requests.post(WIKI_FACTS_URL, json={"wikihow_titles": [[page_title]]}, timeout=1.0).json()
            if res and res[0]["wikihow_content"]:
                page_content = res[0]["wikihow_content"][0]
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)

    return page_content


def get_titles(found_entity_substr, found_entity_types, page_content):
    all_titles = find_all_titles([], page_content)
    titles_we_use = []
    titles_q = {}
    for tp in found_entity_types:
        tp_titles = titles_by_type.get(tp, {})
        titles_we_use += list(tp_titles.keys())
        titles_q = {**titles_q, **tp_titles}
    substr_titles = titles_by_entity_substr.get(found_entity_substr, {})
    titles_we_use += list(substr_titles.keys())
    titles_q = {**titles_q, **substr_titles}
    return titles_q, titles_we_use, all_titles


def get_page_title(vars, entity_substr):
    found_page = ""
    if entity_substr in page_titles_by_entity_substr:
        found_page = page_titles_by_entity_substr[entity_substr]
    else:
        annotations = state_utils.get_last_human_utterance(vars)["annotations"]
        el = annotations.get("entity_linking", [])
        for entity in el:
            if isinstance(entity, dict) and entity["entity_substr"] == entity_substr:
                found_pages_titles = entity["pages_titles"]
                if found_pages_titles:
                    found_page = found_pages_titles[0]
    logger.info(f"found_page {found_page}")
    return found_page


def make_facts_str(paragraphs):
    facts_str = ""
    mentions_list = []
    mention_pages_list = []
    paragraph = ""
    if paragraphs:
        paragraph = paragraphs[0]
    sentences = nltk.sent_tokenize(paragraph)
    sentences_list = []
    cur_len = 0
    max_len = 50
    for sentence in sentences:
        sanitized_sentence, mentions, mention_pages = delete_hyperlinks(sentence)
        words = nltk.word_tokenize(sanitized_sentence)
        if cur_len + len(words) < max_len and not re.findall(WIKI_BADLIST, sanitized_sentence):
            sentences_list.append(sanitized_sentence)
            cur_len += len(words)
            mentions_list += mentions
            mention_pages_list += mention_pages
    if sentences_list:
        facts_str = " ".join(sentences_list)
    cur_len = 0
    if sentences and not sentences_list:
        sentence = sentences[0]
        sanitized_sentence, mentions, mention_pages = delete_hyperlinks(sentence)
        sentence_parts = sanitized_sentence.split(", ")
        mentions_list += mentions
        mention_pages_list += mention_pages
        for part in sentence_parts:
            words = nltk.word_tokenize(part)
            if cur_len + len(words) < max_len and not re.findall(WIKI_BADLIST, part):
                sentences_list.append(part)
                cur_len += len(words)
            facts_str = ", ".join(sentences_list)
            if facts_str and not facts_str.endswith("."):
                facts_str = f"{facts_str}."
    return facts_str, mentions_list, mention_pages_list


def check_utt_cases(vars, utt_info):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    shared_memory = state_utils.get_shared_memory(vars)
    utt_cases = utt_info.get("utt_cases", [])
    if utt_cases:
        for utt_case in utt_cases:
            condition = utt_case["cond"]
            if check_condition(condition, user_uttr, bot_uttr, shared_memory):
                flag = True
    else:
        flag = True
    return flag


def extract_and_save_subtopic(vars, topic_config, found_topic):
    user_uttr = state_utils.get_last_human_utterance(vars)
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    shared_memory = state_utils.get_shared_memory(vars)
    expected_subtopic_info_list = shared_memory.get("expected_subtopic_info", [])
    subtopics = shared_memory.get("subtopics", [])
    for expected_subtopic_info in expected_subtopic_info_list:
        if isinstance(expected_subtopic_info, str) and found_topic:
            global_subtopic_info = topic_config[found_topic].get("expected_subtopics", {})
            if expected_subtopic_info in global_subtopic_info:
                expected_subtopic_info = global_subtopic_info[expected_subtopic_info]
        if isinstance(expected_subtopic_info, dict):
            subtopic = expected_subtopic_info["subtopic"]
            condition = expected_subtopic_info["cond"]
            flag = check_condition(condition, user_uttr, bot_uttr, shared_memory)
            logger.info(f"expected_subtopic_info {expected_subtopic_info} flag {flag}")
            if flag and subtopic not in subtopics:
                subtopics.append(subtopic)
                prev_available_utterances = shared_memory.get("available_utterances", [])
                available_utterances = expected_subtopic_info.get("available_utterances", [])
                for utt_key in available_utterances:
                    if utt_key not in prev_available_utterances:
                        prev_available_utterances.append(utt_key)
                state_utils.save_to_shared_memory(vars, available_utterances=prev_available_utterances)
            if flag:
                state_utils.save_to_shared_memory(vars, subtopics=subtopics)
                state_utils.save_to_shared_memory(vars, expected_subtopic_info={})
                break


def find_trigger(vars, triggers):
    user_uttr = state_utils.get_last_human_utterance(vars)
    annotations = user_uttr["annotations"]
    if "entity_types" in triggers:
        found_entity_substr, found_entity_types, _ = find_entity_by_types(annotations, triggers["entity_types"])
        curr_page = get_page_title(vars, found_entity_substr)
        if curr_page:
            return found_entity_substr, found_entity_types, curr_page, ""
    if "entity_substr" in triggers:
        for entity_info in triggers["entity_substr"]:
            substrings = entity_info["substr"]
            for substr_info in substrings:
                found_substr = check_nounphr(annotations, substr_info["substr"])
                if found_substr:
                    wikipedia_page = substr_info.get("wikipedia_page", "")
                    wikihow_page = substr_info.get("wikihow_page", "")
                    return found_substr, [], wikipedia_page, wikihow_page
    return "", [], "", ""


def delete_topic_info(vars):
    state_utils.save_to_shared_memory(vars, special_topic="")
    state_utils.save_to_shared_memory(vars, expected_subtopic_info={})
    state_utils.save_to_shared_memory(vars, available_utterances=[])
    state_utils.save_to_shared_memory(vars, subtopics=[])
    state_utils.save_to_shared_memory(vars, cur_facts=[])
    state_utils.save_to_shared_memory(vars, used_utt_nums={})
    state_utils.save_to_shared_memory(vars, cur_mode="")
    state_utils.save_to_shared_memory(vars, ackn=[])


def preprocess_wikihow_page(article_content):
    page_content_list = []
    article_content = list(article_content.items())
    for title_num, (title, paragraphs) in enumerate(article_content):
        if title != "intro":
            for n, paragraph in enumerate(paragraphs):
                facts_str = ""
                question = ""
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
                else:
                    cur_len = 0
                    sentence_parts = sentences[0].split(", ")
                    for part in sentence_parts:
                        words = nltk.word_tokenize(part)
                        if cur_len + len(words) < max_len:
                            sentences_list.append(part)
                            cur_len += len(words)
                        facts_str = ", ".join(sentences_list)

                if n == len(paragraphs) - 1 and title_num != len(article_content) - 1:
                    next_title = article_content[title_num + 1][0]
                    question = f"Would you like to know about {next_title.lower()}?"
                elif n != len(paragraphs) - 1:
                    question = random.choice(NEWS_MORE)
                response_dict = {"facts_str": facts_str, "question": question}
                response = f"{facts_str} {question}".strip().replace("  ", " ")
                if response:
                    page_content_list.append(response_dict)
    return page_content_list


def preprocess_wikipedia_page(found_entity_substr, found_entity_types, article_content, predefined_titles=None):
    logger.info(f"found_entity_substr {found_entity_substr} found_entity_types {found_entity_types}")
    titles_q, titles_we_use, all_titles = get_titles(found_entity_substr, found_entity_types, article_content)
    if predefined_titles:
        titles_we_use = predefined_titles
    logger.info(f"titles_we_use {titles_we_use} all_titles {all_titles}")
    facts_list = []
    for n, title in enumerate(titles_we_use):
        page_title = find_page_title(all_titles, title)
        paragraphs = find_paragraph(article_content, page_title)
        logger.info(f"page_title {page_title} paragraphs {paragraphs[:2]}")
        count_par = 0
        for num, paragraph in enumerate(paragraphs):
            facts_str, *_ = make_facts_str([paragraph])
            if facts_str and facts_str.endswith(".") and len(facts_str.split()) > 4:
                facts_list.append((title, facts_str))
                count_par += 1
            if count_par == 2:
                break
    logger.info(f"facts_list {facts_list[:3]}")
    page_content_list = []
    for n, (title, facts_str) in enumerate(facts_list):
        if n != len(facts_list) - 1:
            next_title = facts_list[n + 1][0]
            if next_title != title:
                if found_entity_substr.lower() in next_title.lower():
                    question_template = random.choice(QUESTION_TEMPLATES_SHORT)
                    question = question_template.format(next_title)
                else:
                    question_template = random.choice(QUESTION_TEMPLATES)
                    question = question_template.format(next_title, found_entity_substr)
            else:
                question = random.choice(NEWS_MORE)
            response_dict = {"facts_str": facts_str, "question": question}
            response = f"{facts_str} {question}".strip().replace("  ", " ")
            if response:
                page_content_list.append(response_dict)
        else:
            page_content_list.append(
                {"facts_str": facts_str, "question": f"I was very happy to tell you more about {found_entity_substr}."}
            )
    logger.info(f"page_content_list {page_content_list}")
    return page_content_list


def extract_entity(vars, user_uttr, expected_entity):
    annotations = user_uttr["annotations"]
    if expected_entity:
        logger.info(f"expected_entity {expected_entity}")
        if "cobot_entities_type" in expected_entity:
            cobot_entities_type = expected_entity["cobot_entities_type"]
            nounphrases = annotations.get("cobot_entities", {}).get("labelled_entities", [])
            for nounphr in nounphrases:
                nounphr_text = nounphr.get("text", "")
                nounphr_label = nounphr.get("label", "")
                if nounphr_label == cobot_entities_type:
                    found_entity = nounphr_text
                    return found_entity, {}
        if "wiki_parser_types" in expected_entity:
            types = expected_entity["wiki_parser_types"]
            relations = expected_entity.get("relations", [])
            found_entity, found_types, entity_triplets = find_entity_by_types(annotations, types, relations)
            if found_entity:
                return found_entity, entity_triplets
        if "entity_substr" in expected_entity:
            substr_info_list = expected_entity["entity_substr"]
            for entity, pattern in substr_info_list:
                if re.findall(pattern, user_uttr["text"]):
                    return entity, {}
        if expected_entity.get("any_entity", False):
            cobot_entities = annotations.get("cobot_entities", {}).get("entities", [])
            if cobot_entities:
                return cobot_entities[0], {}
    return "", {}


def extract_and_save_entity(vars, topic_config, found_topic):
    user_uttr = state_utils.get_last_human_utterance(vars)
    shared_memory = state_utils.get_shared_memory(vars)
    expected_entities = shared_memory.get("expected_entities", {})
    found = False
    found_entity = ""
    for expected_entity in expected_entities:
        if isinstance(expected_entity, dict):
            found_entity, entity_triplets = extract_entity(vars, user_uttr, expected_entity)
        elif isinstance(expected_entity, str) and found_topic:
            topic_expected_entities = topic_config[found_topic].get("expected_entities_info", {})
            if expected_entity in topic_expected_entities:
                expected_entity = topic_expected_entities[expected_entity]
                found_entity, entity_triplets = extract_entity(vars, user_uttr, expected_entity)
        logger.info(f"expected_entity {expected_entity} found_entity {found_entity} entity_triplets {entity_triplets}")
        if found_entity:
            entity_name = expected_entity["name"]
            user_info = shared_memory.get("user_info", {})
            new_entity_triplets = shared_memory.get("entity_triplets", {})
            user_info[entity_name] = found_entity
            logger.info(f"extracting entity, user_info {user_info}")
            state_utils.save_to_shared_memory(vars, user_info=user_info)
            if entity_triplets:
                new_entity_triplets = {**new_entity_triplets, **entity_triplets}
                state_utils.save_to_shared_memory(vars, entity_triplets=new_entity_triplets)
            found = True
    if found:
        state_utils.save_to_shared_memory(vars, expected_entities={})


def if_facts_agree(vars):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    shared_memory = state_utils.get_shared_memory(vars)
    cur_facts = shared_memory.get("cur_facts", {})
    for fact in cur_facts:
        condition = fact["cond"]
        flag = check_condition(condition, user_uttr, bot_uttr, shared_memory)
        if flag:
            break
    return flag


def extract_and_save_wikipage(vars, save=False):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    shared_memory = state_utils.get_shared_memory(vars)
    cur_facts = shared_memory.get("cur_facts", {})
    for fact in cur_facts:
        wikihow_page = fact.get("wikihow_page", "")
        condition = fact["cond"]
        checked = check_condition(condition, user_uttr, bot_uttr, shared_memory)
        if checked and wikihow_page:
            flag = True
            if save:
                state_utils.save_to_shared_memory(vars, cur_wikihow_page=wikihow_page)
                state_utils.save_to_shared_memory(vars, cur_facts={})
            break
        wikipedia_page = fact.get("wikipedia_page", "")
        condition = fact["cond"]
        checked = check_condition(condition, user_uttr, bot_uttr, shared_memory)
        if checked and wikipedia_page:
            flag = True
            if save:
                state_utils.save_to_shared_memory(vars, cur_wikipedia_page=wikipedia_page)
                state_utils.save_to_shared_memory(vars, cur_facts={})
            break
    return flag


def check_used_subtopic_utt(vars, topic_config, subtopic):
    flag = False
    shared_memory = state_utils.get_shared_memory(vars)
    found_topic = shared_memory.get("special_topic", "")
    cur_topic_smalltalk = topic_config[found_topic]["smalltalk"]
    used_utt_nums_dict = shared_memory.get("used_utt_nums", {})
    used_utt_nums = used_utt_nums_dict.get(found_topic, [])
    total, used = 0, 0
    if found_topic:
        for num, utt_info in enumerate(cur_topic_smalltalk):
            if utt_info.get("subtopic", "") == subtopic:
                total += 1
                if num in used_utt_nums:
                    used += 1
        logger.info(
            f"check_used_subtopic_utt, subtopic {subtopic} total {total} used {used} "
            f"used_utt_nums_dict {used_utt_nums_dict}"
        )
        if total > 0 and total == used:
            flag = True
    return flag


def make_resp_list(vars, utt_list, topic_config, shared_memory):
    resp_list = []
    found_topic = shared_memory.get("special_topic", "")
    user_info = shared_memory.get("user_info", {})
    logger.info(f"make_smalltalk_response, user_info {user_info}")
    for utt in utt_list:
        utt_slots = re.findall(r"{(.*?)}", utt)
        if not utt_slots:
            resp_list.append(utt)
        else:
            entity_triplets = shared_memory.get("entity_triplets", {})
            for slot in utt_slots:
                slot_value = ""
                if slot.startswith("["):
                    slot_strip = slot.strip("[]")
                    slot_keys = slot_strip.split(", ")
                    bot_data = topic_config.get(found_topic, {}).get("bot_data", {})
                    if slot_keys and slot_keys[0] == "bot_data" and bot_data:
                        slot_value = bot_data
                        for key in slot_keys[1:]:
                            if key in user_info:
                                key = user_info[key]
                            slot_value = slot_value[key]
                    elif slot_keys and slot_keys[0] != "bot_data" and slot_keys[0] in user_info:
                        user_var_name = slot_keys[0]
                        user_var_val = user_info[user_var_name]
                        relation = slot_keys[1]
                        objects = entity_triplets.get(user_var_val, {}).get(relation, "")
                        if len(objects) == 1:
                            slot_value = objects[0]
                        elif len(objects) == 2:
                            slot_value = f"{objects[0]} and {objects[1]}"
                        elif len(objects) > 2:
                            slot_value = ", ".join(objects[:2]) + " and " + objects[2]
                        slot_value = slot_value.strip().replace("  ", " ")
                else:
                    slot_value = user_info.get(slot, "")
                if slot_value:
                    slot_repl = "{" + slot + "}"
                    utt = utt.replace(slot_repl, slot_value)
            if "{" not in utt:
                resp_list.append(utt)
    return resp_list


def check_acknowledgements(vars, topic_config):
    response = ""
    user_uttr = state_utils.get_last_human_utterance(vars)
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    shared_memory = state_utils.get_shared_memory(vars)
    found_topic = shared_memory.get("special_topic", "")
    if found_topic:
        ackns = topic_config[found_topic].get("ackn", [])
        for ackn in ackns:
            condition = ackn["cond"]
            if check_condition(condition, user_uttr, bot_uttr, shared_memory):
                answer = ackn["answer"]
                resp_list = make_resp_list(vars, answer, topic_config, shared_memory)
                if resp_list:
                    response = " ".join(resp_list).strip().replace("  ", " ")
                    break
    return response


def answer_users_question(vars, topic_config):
    shared_memory = state_utils.get_shared_memory(vars)
    found_topic = shared_memory.get("special_topic", "")
    answer = ""
    user_uttr = state_utils.get_last_human_utterance(vars)
    if found_topic:
        questions = topic_config[found_topic].get("questions", [])
        logger.info(f"user_uttr {user_uttr.get('text', '')} questions {questions}")
        for question in questions:
            pattern = question["pattern"]
            if re.findall(pattern, user_uttr["text"]):
                answer = question["answer"]
                break
    return answer


def check_switch(vars, topic_config):
    user_uttr = state_utils.get_last_human_utterance(vars)
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    shared_memory = state_utils.get_shared_memory(vars)
    found_topic = shared_memory.get("special_topic", "")
    first_utt = False
    utt_can_continue = "can"
    utt_conf = 0.0
    shared_memory = state_utils.get_shared_memory(vars)
    for topic in topic_config:
        linkto = topic_config[topic].get("linkto", [])
        for phrase in linkto:
            if phrase.lower() in bot_uttr["text"].lower():
                found_topic = topic
                first_utt = True
                break
        pattern = topic_config[topic].get("pattern", "")
        if pattern:
            if if_chat_about_particular_topic(user_uttr, bot_uttr, compiled_pattern=pattern):
                utt_can_continue = "must"
                utt_conf = 1.0
                found_topic = topic
                first_utt = True
            elif re.findall(pattern, user_uttr["text"]) and not found_topic:
                utt_can_continue = "prompt"
                utt_conf = 0.95
                found_topic = topic
                first_utt = True
        switch_on = topic_config[topic].get("switch_on", [])
        for switch_elem in switch_on:
            condition = switch_elem["cond"]
            if check_condition(condition, user_uttr, bot_uttr, shared_memory):
                found_topic = topic
                utt_can_continue = switch_elem.get("can_continue", "can")
                utt_conf = switch_elem.get("conf", utt_conf)
                first_utt = True
                break
        if found_topic:
            break
    return found_topic, first_utt, utt_can_continue, utt_conf


def start_or_continue_scenario(vars, topic_config):
    flag = False
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    prev_active_skill = bot_uttr.get("active_skill", "")
    shared_memory = state_utils.get_shared_memory(vars)
    isno = is_no(state_utils.get_last_human_utterance(vars))
    cur_mode = shared_memory.get("cur_mode", "smalltalk")
    found_topic = shared_memory.get("special_topic", "")
    logger.info(f"special_topic_request, found_topic {found_topic}")
    user_info = shared_memory.get("user_info", {})
    entity_triplets = shared_memory.get("entity_triplets", {})
    logger.info(f"start_or_continue_scenario, user_info {user_info}, entity_triplets {entity_triplets}")
    if cur_mode == "facts" and isno:
        cur_mode = "smalltalk"
    first_utt = False
    if not found_topic or prev_active_skill not in {"dff_wiki_skill", "dff_music_skill"}:
        found_topic, first_utt, utt_can_continue, utt_conf = check_switch(vars, topic_config)
        logger.info(f"start_or_continue_scenario, {found_topic}, {first_utt}")
    if found_topic:
        cur_topic_smalltalk = topic_config[found_topic].get("smalltalk", [])
        used_utt_nums = shared_memory.get("used_utt_nums", {}).get("found_topic", [])
        logger.info(f"used_smalltalk {used_utt_nums}")
        if cur_topic_smalltalk and len(used_utt_nums) < len(cur_topic_smalltalk) and cur_mode == "smalltalk":
            flag = True
        if not first_utt and (
            (found_topic != "music" and prev_active_skill != "dff_wiki_skill")
            or (found_topic == "music" and prev_active_skill != "dff_music_skill")
        ):
            flag = False
    return flag


def make_smalltalk_response(vars, topic_config, shared_memory, utt_info, used_utt_nums, num):
    user_uttr = state_utils.get_last_human_utterance(vars)
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    response = ""
    utt_list = utt_info["utt"]
    found_ackn = ""
    ackns = utt_info.get("ackn", [])
    for ackn in ackns:
        condition = ackn["cond"]
        if check_condition(condition, user_uttr, bot_uttr, shared_memory):
            found_ackn = ackn["answer"]
            break
    found_prev_ackn = ""
    ackns = shared_memory.get("ackn", [])
    for ackn in ackns:
        condition = ackn["cond"]
        if check_condition(condition, user_uttr, bot_uttr, shared_memory):
            found_prev_ackn = ackn["answer"]
            break
    found_ackn = found_ackn or found_prev_ackn
    resp_list = make_resp_list(vars, utt_list, topic_config, shared_memory)
    if resp_list:
        response = " ".join(resp_list).strip().replace("  ", " ")
        used_utt_nums.append(num)
        cur_facts = utt_info.get("facts", {})
        state_utils.save_to_shared_memory(vars, cur_facts=cur_facts)
        next_ackn = utt_info.get("next_ackn", [])
        state_utils.save_to_shared_memory(vars, ackn=next_ackn)
        expected_entities = utt_info.get("expected_entities", {})
        if expected_entities:
            state_utils.save_to_shared_memory(vars, expected_entities=expected_entities)
        expected_subtopic_info = utt_info.get("expected_subtopic_info", {})
        logger.info(f"print expected_subtopic_info {expected_subtopic_info} utt_info {utt_info}")
        state_utils.save_to_shared_memory(vars, expected_subtopic_info=expected_subtopic_info)
        if found_ackn:
            found_ackn_sentences = nltk.sent_tokenize(found_ackn)
            found_ackn_list = make_resp_list(vars, found_ackn_sentences, topic_config, shared_memory)
            found_ackn = " ".join(found_ackn_list)
        response = f"{found_ackn} {response}".strip().replace("  ", " ")
    return response, used_utt_nums


def smalltalk_response(vars, topic_config):
    response = ""
    first_utt = False
    shared_memory = state_utils.get_shared_memory(vars)
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    prev_active_skill = bot_uttr.get("active_skill", "")
    if prev_active_skill not in {"dff_wiki_skill", "dff_music_skill"}:
        delete_topic_info(vars)
    found_topic = shared_memory.get("special_topic", "")
    cur_mode = shared_memory.get("cur_mode", "smalltalk")
    isno = is_no(state_utils.get_last_human_utterance(vars))
    utt_can_continue = "can"
    utt_conf = 0.0
    if cur_mode == "facts" and isno:
        state_utils.save_to_shared_memory(vars, cur_wikihow_page="")
        state_utils.save_to_shared_memory(vars, cur_wikipedia_page="")
        memory["wikihow_content"] = []
        memory["wikipedia_content"] = []
    if not found_topic:
        found_topic, first_utt, utt_can_continue, utt_conf = check_switch(vars, topic_config)
    if found_topic:
        expected_entities = topic_config[found_topic].get("expected_entities", {})
        if expected_entities:
            state_utils.save_to_shared_memory(vars, expected_entities=expected_entities)
        existing_subtopic_info = shared_memory.get("expected_subtopic_info", [])
        expected_subtopic_info = topic_config[found_topic].get("expected_subtopic_info", {})
        if expected_subtopic_info and not existing_subtopic_info and first_utt:
            state_utils.save_to_shared_memory(vars, expected_subtopic_info=expected_subtopic_info)

    extract_and_save_entity(vars, topic_config, found_topic)
    extract_and_save_subtopic(vars, topic_config, found_topic)
    available_utterances = shared_memory.get("available_utterances", [])
    logger.info(f"subtopics {shared_memory.get('subtopics', [])}")
    subtopics_to_delete = 0
    add_general_ackn = False
    if found_topic:
        used_utt_nums_dict = shared_memory.get("used_utt_nums", {})
        used_utt_nums = used_utt_nums_dict.get(found_topic, [])
        state_utils.save_to_shared_memory(vars, special_topic=found_topic)
        subtopics = shared_memory.get("subtopics", [])
        if subtopics:
            for i in range(len(subtopics) - 1, -1, -1):
                cur_subtopic = subtopics[i]
                for num, utt_info in enumerate(topic_config[found_topic]["smalltalk"]):
                    utt_key = utt_info.get("key", "")
                    if num not in used_utt_nums and (
                        not available_utterances or (available_utterances and utt_key in available_utterances)
                    ):
                        if utt_info.get("subtopic", "") == cur_subtopic and check_utt_cases(vars, utt_info):
                            response, used_utt_nums = make_smalltalk_response(
                                vars, topic_config, shared_memory, utt_info, used_utt_nums, num
                            )
                            if response:
                                add_general_ackn = utt_info.get("add_general_ackn", False)
                                utt_can_continue = utt_info.get("can_continue", "can")
                                utt_conf = utt_info.get("conf", utt_conf)
                                break
                if response:
                    used_utt_nums_dict[found_topic] = used_utt_nums
                    state_utils.save_to_shared_memory(vars, used_utt_nums=used_utt_nums_dict)
                    if check_used_subtopic_utt(vars, topic_config, cur_subtopic):
                        subtopics_to_delete += 1
                    break
                else:
                    subtopics_to_delete += 1
        if not subtopics or not response:
            for num, utt_info in enumerate(topic_config[found_topic]["smalltalk"]):
                utt_key = utt_info.get("key", "")
                if (
                    num not in used_utt_nums
                    and check_utt_cases(vars, utt_info)
                    and not utt_info.get("subtopic", "")
                    and (not available_utterances or (available_utterances and utt_key in available_utterances))
                ):
                    response, used_utt_nums = make_smalltalk_response(
                        vars, topic_config, shared_memory, utt_info, used_utt_nums, num
                    )
                    if response:
                        utt_can_continue = utt_info.get("can_continue", "can")
                        utt_conf = utt_info.get("conf", utt_conf)
                        add_general_ackn = utt_info.get("add_general_ackn", False)
                        used_utt_nums_dict[found_topic] = used_utt_nums
                        state_utils.save_to_shared_memory(vars, used_utt_nums=used_utt_nums_dict)
                        break
        if subtopics_to_delete:
            for i in range(subtopics_to_delete):
                subtopics.pop()
            state_utils.save_to_shared_memory(vars, subtopics=subtopics)

        logger.info(f"used_utt_nums_dict {used_utt_nums_dict} used_utt_nums {used_utt_nums}")
    acknowledgement = check_acknowledgements(vars, topic_config)
    answer = answer_users_question(vars, topic_config) or acknowledgement
    response = f"{answer} {response}".strip().replace("  ", " ")
    logger.info(f"response {response}")
    if response:
        state_utils.save_to_shared_memory(vars, cur_mode="smalltalk")
        if utt_conf > 0.0:
            state_utils.set_confidence(vars, confidence=utt_conf)
        else:
            state_utils.set_confidence(vars, confidence=CONF_DICT["WIKI_TOPIC"])
        if first_utt or utt_can_continue == "must":
            state_utils.set_can_continue(vars, continue_flag=common_constants.MUST_CONTINUE)
        elif utt_can_continue == "prompt":
            state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_PROMPT)
        else:
            state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    else:
        state_utils.set_confidence(vars, confidence=CONF_DICT["UNDEFINED"])
        state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_NOT_CONTINUE)
    if not add_general_ackn:
        state_utils.add_acknowledgement_to_response_parts(vars)
    return response


def start_or_continue_facts(vars, topic_config):
    flag = False
    shared_memory = state_utils.get_shared_memory(vars)
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    prev_active_skill = bot_uttr.get("active_skill", "")
    isno = is_no(state_utils.get_last_human_utterance(vars))
    found_topic = shared_memory.get("special_topic", "")
    cur_mode = shared_memory.get("cur_mode", "smalltalk")
    cur_wikipedia_page = shared_memory.get("cur_wikipedia_page", "")
    cur_wikihow_page = shared_memory.get("cur_wikihow_page", "")
    logger.info(f"cur_wikihow_page {cur_wikihow_page} cur_wikipedia_page {cur_wikipedia_page}")
    if found_topic:
        if cur_mode == "smalltalk" and "triggers" in topic_config[found_topic]:
            triggers = topic_config[found_topic]["triggers"]
            entity_substr, entity_types, wikipedia_page, wikihow_page = find_trigger(vars, triggers)
            if wikihow_page or wikipedia_page or if_facts_agree(vars):
                flag = True
        else:
            checked_wikipage = extract_and_save_wikipage(vars)
            if checked_wikipage:
                flag = True
            if (cur_wikipedia_page or cur_wikihow_page) and not isno:
                wikihow_page_content_list = memory.get("wikihow_content", [])
                wikipedia_page_content_list = memory.get("wikipedia_content", [])
                used_wikihow_nums = shared_memory.get("used_wikihow_nums", {}).get(cur_wikihow_page, [])
                used_wikipedia_nums = shared_memory.get("used_wikipedia_nums", {}).get(cur_wikipedia_page, [])
                logger.info(f"request, used_wikihow_nums {used_wikihow_nums} used_wikipedia_nums {used_wikipedia_nums}")
                logger.info(
                    f"request, wikipedia_page_content_list {wikipedia_page_content_list[:3]} "
                    f"wikihow_page_content_list {wikihow_page_content_list[:3]}"
                )
                if len(wikihow_page_content_list) > 0 and len(used_wikihow_nums) < len(wikihow_page_content_list):
                    flag = True
                if len(wikipedia_page_content_list) > 0 and len(used_wikipedia_nums) < len(wikipedia_page_content_list):
                    flag = True

    first_utt = False
    if not shared_memory.get("special_topic", "") or prev_active_skill not in {"dff_wiki_skill", "dff_music_skill"}:
        found_topic, first_utt, utt_can_continue, utt_conf = check_switch(vars, topic_config)
    logger.info(f"start_or_continue_facts, first_utt {first_utt}")
    if found_topic:
        facts = topic_config[found_topic].get("facts", {})
        if facts:
            flag = True
        if not first_utt and (
            (found_topic != "music" and prev_active_skill != "dff_wiki_skill")
            or (found_topic == "music" and prev_active_skill != "dff_music_skill")
        ):
            flag = False
    return flag


def facts_response(vars, topic_config, wikihow_cache, wikipedia_cache):
    shared_memory = state_utils.get_shared_memory(vars)
    user_uttr = state_utils.get_last_human_utterance(vars)
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    prev_active_skill = bot_uttr.get("active_skill", "")
    if prev_active_skill not in {"dff_wiki_skill", "dff_music_skill"}:
        delete_topic_info(vars)
    isyes = is_yes(user_uttr) or re.findall(CONTINUE_PATTERN, user_uttr["text"])
    response = ""
    cur_mode = shared_memory.get("cur_mode", "smalltalk")
    wikipedia_page = shared_memory.get("cur_wikipedia_page", "")
    wikihow_page = shared_memory.get("cur_wikihow_page", "")
    found_topic = shared_memory.get("special_topic", "")
    utt_can_continue = common_constants.CAN_CONTINUE_SCENARIO
    utt_conf = CONF_DICT["WIKI_TOPIC"]
    first_utt = False
    entity_substr = ""
    entity_types = []
    if not found_topic:
        found_topic, first_utt, utt_can_continue, utt_conf = check_switch(vars, topic_config)
    extract_and_save_entity(vars, topic_config, found_topic)
    extract_and_save_subtopic(vars, topic_config, found_topic)
    extract_and_save_wikipage(vars, True)
    if found_topic and cur_mode == "smalltalk":
        if "triggers" in topic_config[found_topic]:
            triggers = topic_config[found_topic]["triggers"]
            entity_substr, entity_types, wikipedia_page, wikihow_page = find_trigger(vars, triggers)
        facts = topic_config[found_topic].get("facts", {})
        if facts and not wikihow_page and not wikipedia_page:
            entity_substr = facts.get("entity_substr", "")
            entity_types = facts.get("entity_types", [])
            wikihow_page = facts.get("wikihow_page", "")
            wikipedia_page = facts.get("wikipedia_page", "")
            logger.info(f"wikipedia_page {wikipedia_page}")
        if not wikihow_page:
            wikihow_page = shared_memory.get("cur_wikihow_page", "")
        if wikihow_page:
            if wikihow_page in wikihow_cache:
                page_content = wikihow_cache[wikihow_page]
            else:
                page_content = get_wikihow_content(wikihow_page)
            wikihow_page_content_list = preprocess_wikihow_page(page_content)
            memory["wikihow_content"] = wikihow_page_content_list
            state_utils.save_to_shared_memory(vars, cur_wikihow_page=wikihow_page)
        if not wikipedia_page:
            wikipedia_page = shared_memory.get("cur_wikipedia_page", "")

        if wikipedia_page:
            if wikipedia_page in wikipedia_cache:
                page_content = wikipedia_cache[wikipedia_page].get("page_content", {})
            else:
                page_content, _ = get_page_content(wikipedia_page)
            if not entity_substr:
                entity_substr = wikipedia_page.lower()
            titles_info = topic_config[found_topic].get("titles_info", [])
            predefined_titles = []
            for titles_info_elem in titles_info:
                if wikipedia_page in titles_info_elem["pages"]:
                    predefined_titles = titles_info_elem["titles"]
                    break
            wikipedia_page_content_list = preprocess_wikipedia_page(
                entity_substr, entity_types, page_content, predefined_titles
            )
            memory["wikipedia_content"] = wikipedia_page_content_list
            state_utils.save_to_shared_memory(vars, cur_wikipedia_page=wikipedia_page)
        logger.info(f"wikihow_page {wikihow_page} wikipedia_page {wikipedia_page}")
    if found_topic:
        used_wikihow_nums_dict = shared_memory.get("used_wikihow_nums", {})
        used_wikihow_nums = used_wikihow_nums_dict.get(wikihow_page, [])
        used_wikipedia_nums_dict = shared_memory.get("used_wikipedia_nums", {})
        used_wikipedia_nums = used_wikipedia_nums_dict.get(wikipedia_page, [])
        wikihow_page_content_list = memory.get("wikihow_content", [])
        wikipedia_page_content_list = memory.get("wikipedia_content", [])
        logger.info(f"response, used_wikihow_nums {used_wikihow_nums} used_wikipedia_nums {used_wikipedia_nums}")
        logger.info(
            f"response, wikipedia_page_content_list {wikipedia_page_content_list[:3]} "
            f"wikihow_page_content_list {wikihow_page_content_list[:3]}"
        )
        if wikihow_page and wikihow_page_content_list:
            for num, fact in enumerate(wikihow_page_content_list):
                if num not in used_wikihow_nums:
                    facts_str = fact.get("facts_str", "")
                    question = fact.get("question", "")
                    response = f"{facts_str} {question}".strip().replace("  ", " ")
                    used_wikihow_nums.append(num)
                    used_wikihow_nums_dict[wikihow_page] = used_wikihow_nums
                    state_utils.save_to_shared_memory(vars, used_wikihow_nums=used_wikihow_nums_dict)
                    break
        if not response and wikipedia_page and wikipedia_page_content_list:
            for num, fact in enumerate(wikipedia_page_content_list):
                if num not in used_wikipedia_nums:
                    facts_str = fact.get("facts_str", "")
                    question = fact.get("question", "")
                    response = f"{facts_str} {question}".strip().replace("  ", " ")
                    used_wikipedia_nums.append(num)
                    used_wikipedia_nums_dict[wikipedia_page] = used_wikipedia_nums
                    state_utils.save_to_shared_memory(vars, used_wikipedia_nums=used_wikipedia_nums_dict)
                    break
        cur_mode = "facts"
        if len(wikihow_page_content_list) == len(used_wikihow_nums) and len(wikipedia_page_content_list) == len(
            used_wikipedia_nums
        ):
            cur_mode = "smalltalk"
            if len(wikihow_page_content_list) == len(used_wikihow_nums):
                state_utils.save_to_shared_memory(vars, cur_wikihow_page="")
                memory["wikihow_content"] = []
            if len(wikipedia_page_content_list) == len(used_wikipedia_nums):
                state_utils.save_to_shared_memory(vars, cur_wikipedia_page="")
                memory["wikipedia_content"] = []

    answer = answer_users_question(vars, topic_config)
    response = f"{answer} {response}".strip().replace("  ", " ")
    if not shared_memory.get("special_topic", ""):
        found_topic, first_utt, utt_can_continue, utt_conf = check_switch(vars, topic_config)
        state_utils.save_to_shared_memory(vars, special_topic=found_topic)
    if response:
        state_utils.save_to_shared_memory(vars, cur_mode=cur_mode)
        state_utils.set_confidence(vars, confidence=utt_conf)
        if isyes or (first_utt and utt_can_continue == "must"):
            state_utils.set_can_continue(vars, continue_flag=common_constants.MUST_CONTINUE)
        else:
            state_utils.set_can_continue(vars, continue_flag=utt_can_continue)
    else:
        state_utils.set_confidence(vars, confidence=CONF_DICT["UNDEFINED"])
        state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_NOT_CONTINUE)
    state_utils.add_acknowledgement_to_response_parts(vars)
    return response
