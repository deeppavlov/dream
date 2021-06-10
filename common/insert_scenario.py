import logging
import os
import random
import re
import nltk
import requests
import sentry_sdk
import common.constants as common_constants
import common.dialogflow_framework.utils.state as state_utils

from common.wiki_skill import find_entity_by_types, check_nounphr, find_page_title, find_paragraph, \
    delete_hyperlinks, find_all_titles, used_types_dict, NEWS_MORE, WIKI_BLACKLIST, QUESTION_TEMPLATES, \
    CONF_DICT
from common.utils import is_no, is_yes

sentry_sdk.init(os.getenv('SENTRY_DSN'))
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
                found_pages_titles = entity["entity_pages_titles"]
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
        if cur_len + len(words) < max_len and not re.findall(WIKI_BLACKLIST, sanitized_sentence):
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
            if cur_len + len(words) < max_len and not re.findall(WIKI_BLACKLIST, part):
                sentences_list.append(part)
                cur_len += len(words)
            facts_str = ", ".join(sentences_list)
            if facts_str and not facts_str.endswith("."):
                facts_str = f"{facts_str}."
    return facts_str, mentions_list, mention_pages_list


def check_condition_element(vars, elem, user_uttr, bot_uttr):
    flag = False
    annotations = user_uttr["annotations"]
    isyes = is_yes(state_utils.get_last_human_utterance(vars))
    isno = is_no(state_utils.get_last_human_utterance(vars))
    if elem[0] == "is_yes" and isyes:
        flag = True
    elif elem[0] == "is_no" and isno:
        flag = True
    elif "pattern" in elem[0]:
        pattern = elem[0]["pattern"]
        if elem[1] == "user" and re.findall(pattern, user_uttr["text"], re.IGNORECASE):
            flag = True
        if elem[1] == "bot" and re.findall(pattern, bot_uttr["text"], re.IGNORECASE):
            flag = True
    elif "cobot_entities_type" in elem[0]:
        cobot_entities_type = elem[0]["cobot_entities_type"]
        nounphrases = annotations.get("cobot_entities", {}).get("labelled_entities", [])
        for nounphr in nounphrases:
            nounphr_label = nounphr.get("label", "")
            if nounphr_label == cobot_entities_type:
                flag = True
    elif "wiki_parser_types" in elem[0]:
        wp_types = elem[0]["wp_types"]
        found_entity, found_types = find_entity_by_types(annotations, wp_types)
        if found_entity:
            flag = True
    if not elem[2]:
        flag = not flag
    return flag


def check_condition(vars, condition, user_uttr, bot_uttr):
    flag = False
    checked_elements = []
    for elem in condition:
        if isinstance(elem[0], str) or isinstance(elem[0], dict):
            flag = check_condition_element(vars, elem, user_uttr, bot_uttr)
        elif isinstance(elem[0], list):
            flag = all([check_condition_element(vars, sub_elem, user_uttr, bot_uttr) for sub_elem in elem])
        checked_elements.append(flag)
    if any(checked_elements):
        flag = True
    return flag


def check_utt_cases(vars, utt_info):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    utt_cases = utt_info.get("utt_cases", [])
    if utt_cases:
        for utt_case in utt_cases:
            condition = utt_case["cond"]
            if check_condition(vars, condition, user_uttr, bot_uttr):
                flag = True
    else:
        flag = True
    return flag


def extract_and_save_subtopic(vars):
    user_uttr = state_utils.get_last_human_utterance(vars)
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    shared_memory = state_utils.get_shared_memory(vars)
    expected_subtopic_info_list = shared_memory.get("expected_subtopic_info", [])
    subtopics = shared_memory.get("subtopics", [])
    for expected_subtopic_info in expected_subtopic_info_list:
        subtopic = expected_subtopic_info["subtopic"]
        condition = expected_subtopic_info["cond"]
        flag = check_condition(vars, condition, user_uttr, bot_uttr)
        if subtopic not in subtopics:
            subtopics.append(subtopic)
        if flag:
            state_utils.save_to_shared_memory(vars, subtopics=subtopics)
            state_utils.save_to_shared_memory(vars, expected_subtopic_info={})
            break


def find_trigger(vars, triggers):
    user_uttr = state_utils.get_last_human_utterance(vars)
    annotations = user_uttr["annotations"]
    if "entity_types" in triggers:
        found_entity_substr, found_entity_types = find_entity_by_types(annotations, triggers["entity_types"])
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
                response = f"{facts_str} {question}".strip().replace("  ", " ")
                if response:
                    page_content_list.append(response)
    return page_content_list


def preprocess_wikipedia_page(found_entity_substr, found_entity_types, article_content):
    logger.info(f"found_entity_substr {found_entity_substr} found_entity_types {found_entity_types}")
    titles_q, titles_we_use, all_titles = get_titles(found_entity_substr, found_entity_types, article_content)
    logger.info(f"titles_we_use {titles_we_use} all_titles {all_titles}")
    facts_list = []
    for n, title in enumerate(titles_we_use):
        page_title = find_page_title(all_titles, title)
        paragraphs = find_paragraph(article_content, page_title)
        logger.info(f"page_title {page_title} paragraphs {paragraphs}")
        facts_str, _, _ = make_facts_str(paragraphs)
        logger.info(f"facts_str {facts_str}")
        if facts_str:
            facts_list.append((title, facts_str))
    logger.info(f"facts_list {facts_list}")
    page_content_list = []
    for n, (title, facts_str) in enumerate(facts_list):
        if n != len(facts_list) - 1:
            next_title = facts_list[n + 1][0]
            question_template = random.choice(QUESTION_TEMPLATES)
            question = question_template.format(next_title, found_entity_substr)
            response = f"{facts_str} {question}".strip().replace("  ", " ")
            if response:
                page_content_list.append(response)
        else:
            page_content_list.append(facts_str)
    logger.info(f"page_content_list {page_content_list}")
    return page_content_list


def extract_entity(vars):
    user_uttr = state_utils.get_last_human_utterance(vars)
    annotations = user_uttr["annotations"]
    shared_memory = state_utils.get_shared_memory(vars)
    expected_entity = shared_memory.get("expected_entity", {})
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
                    return found_entity
        if "wiki_parser_types" in expected_entity:
            found_entity, found_types = find_entity_by_types(annotations, expected_entity["wiki_parser_types"])
            return found_entity
        if expected_entity.get("any_entity", False):
            cobot_entities = annotations.get("cobot_entities", {}).get("entities", [])
            if cobot_entities:
                return cobot_entities[0]
    return ""


def extract_and_save_entity(vars):
    shared_memory = state_utils.get_shared_memory(vars)
    expected_entity = shared_memory.get("expected_entity", {})
    if expected_entity:
        found_entity = extract_entity(vars)
        if found_entity:
            entity_name = expected_entity["name"]
            user_info = shared_memory.get("user_info", {})
            user_info[entity_name] = found_entity
            state_utils.save_to_shared_memory(vars, user_info=user_info)
            state_utils.save_to_shared_memory(vars, expected_entity={})


def if_facts_agree(vars):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    shared_memory = state_utils.get_shared_memory(vars)
    cur_facts = shared_memory.get("cur_facts", {})
    for fact in cur_facts:
        condition = fact["cond"]
        flag = check_condition(vars, condition, user_uttr, bot_uttr)
        if flag:
            break
    return flag


def extract_and_save_wikipage(vars):
    user_uttr = state_utils.get_last_human_utterance(vars)
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    shared_memory = state_utils.get_shared_memory(vars)
    cur_facts = shared_memory.get("cur_facts", {})
    for fact in cur_facts:
        wikihow_page = fact.get("wikihow_page", "")
        condition = fact["cond"]
        flag = check_condition(vars, condition, user_uttr, bot_uttr)
        if flag and wikihow_page:
            state_utils.save_to_shared_memory(vars, cur_wikihow_page=wikihow_page)
            state_utils.save_to_shared_memory(vars, cur_facts={})
            break


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
        logger.info(f"check_used_subtopic_utt, subtopic {subtopic} total {total} used {used} "
                    f"used_utt_nums_dict {used_utt_nums_dict}")
        if total > 0 and total == used:
            flag = True
    return flag


def answer_users_question(vars, topic_config):
    shared_memory = state_utils.get_shared_memory(vars)
    found_topic = shared_memory.get("special_topic", "")
    answer = ""
    user_uttr = state_utils.get_last_human_utterance(vars)
    if found_topic:
        questions = topic_config[found_topic]["questions"]
        logger.info(f"user_uttr {user_uttr} questions {questions}")
        for question in questions:
            pattern = question["pattern"]
            if re.findall(pattern, user_uttr["text"]):
                answer = question["answer"]
                break
    return answer


def start_or_continue_scenario(vars, topic_config):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    shared_memory = state_utils.get_shared_memory(vars)
    isno = is_no(state_utils.get_last_human_utterance(vars))
    cur_mode = shared_memory.get("cur_mode", "smalltalk")
    found_topic = shared_memory.get("special_topic", "")
    logger.info(f"special_topic_request, found_topic {found_topic}")
    if cur_mode == "facts" and isno:
        cur_mode = "smalltalk"
    if not found_topic:
        for topic in topic_config:
            linkto = topic_config[topic].get("linkto", [])
            pattern = topic_config[topic]["pattern"]
            for phrase in linkto:
                if phrase.lower() in bot_uttr["text"].lower():
                    found_topic = topic
                    break
            if re.findall(pattern, user_uttr["text"]):
                found_topic = topic
            if found_topic:
                break
    if found_topic:
        cur_topic_smalltalk = topic_config[found_topic]["smalltalk"]
        used_utt_nums = shared_memory.get("used_utt_nums", {}).get("found_topic", [])
        logger.info(f"used_smalltalk {used_utt_nums}")
        if len(used_utt_nums) < len(cur_topic_smalltalk) and cur_mode == "smalltalk":
            flag = True
    return flag


def make_smalltalk_response(vars, shared_memory, utt_info, used_utt_nums, num):
    response = ""
    utt_list = utt_info["utt"]
    resp_list = []
    for utt in utt_list:
        utt_slots = re.findall(r"{(.*?)}", utt)
        logger.info(f"utt_slots {utt_slots}")
        if utt_slots and any([not shared_memory.get("user_info", {}).get(slot, "")
                              for slot in utt_slots]):
            pass
        elif not utt_slots:
            resp_list.append(utt)
        else:
            for slot in utt_slots:
                slot_value = shared_memory.get("user_info", {}).get(slot, "")
                slot_repl = "{" + slot + "}"
                utt = utt.replace(slot_repl, slot_value)
            resp_list.append(utt)
    if resp_list:
        response = " ".join(resp_list).strip().replace("  ", " ")
        used_utt_nums.append(num)
        cur_facts = utt_info.get("facts", {})
        state_utils.save_to_shared_memory(vars, cur_facts=cur_facts)
        expected_entity = utt_info.get("expected_entity", {})
        if expected_entity:
            state_utils.save_to_shared_memory(vars, expected_entity=expected_entity)
        expected_subtopic_info = utt_info.get("expected_subtopic_info", {})
        if expected_subtopic_info:
            state_utils.save_to_shared_memory(vars, expected_subtopic_info=expected_subtopic_info)
    return response, used_utt_nums


def smalltalk_response(vars, topic_config):
    response = ""
    first_utt = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    shared_memory = state_utils.get_shared_memory(vars)
    found_topic = shared_memory.get("special_topic", "")
    cur_mode = shared_memory.get("cur_mode", "smalltalk")
    isno = is_no(state_utils.get_last_human_utterance(vars))
    if cur_mode == "facts" and isno:
        state_utils.save_to_shared_memory(vars, cur_wikihow_page="")
        state_utils.save_to_shared_memory(vars, cur_wikipedia_page="")
        memory["wikihow_content"] = []
        memory["wikipedia_content"] = []
    if not found_topic:
        for topic in topic_config:
            linkto = topic_config[topic].get("linkto", [])
            pattern = topic_config[topic]["pattern"]
            for phrase in linkto:
                if phrase.lower() in bot_uttr["text"].lower():
                    found_topic = topic
                    first_utt = True
                    break
            if re.findall(pattern, user_uttr["text"]):
                found_topic = topic
                first_utt = True
            if found_topic:
                break

    extract_and_save_entity(vars)
    extract_and_save_subtopic(vars)
    subtopics_to_delete = 0
    if found_topic:
        used_utt_nums_dict = shared_memory.get("used_utt_nums", {})
        used_utt_nums = used_utt_nums_dict.get(found_topic, [])
        state_utils.save_to_shared_memory(vars, special_topic=found_topic)
        subtopics = shared_memory.get("subtopics", [])
        if subtopics:
            for i in range(len(subtopics) - 1, -1, -1):
                cur_subtopic = subtopics[i]
                for num, utt_info in enumerate(topic_config[found_topic]["smalltalk"]):
                    if num not in used_utt_nums:
                        if utt_info.get("subtopic", "") == cur_subtopic and check_utt_cases(vars, utt_info):
                            response, used_utt_nums = make_smalltalk_response(vars, shared_memory, utt_info,
                                                                              used_utt_nums, num)
                            if response:
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
                if num not in used_utt_nums and check_utt_cases(vars, utt_info):
                    response, used_utt_nums = make_smalltalk_response(vars, shared_memory, utt_info, used_utt_nums, num)
                    if response:
                        used_utt_nums_dict[found_topic] = used_utt_nums
                        state_utils.save_to_shared_memory(vars, used_utt_nums=used_utt_nums_dict)
                        break
        if subtopics_to_delete:
            for i in range(subtopics_to_delete):
                subtopics.pop()
            state_utils.save_to_shared_memory(vars, subtopics=subtopics)

        logger.info(f"used_utt_nums_dict {used_utt_nums_dict} used_utt_nums {used_utt_nums}")
    answer = answer_users_question(vars, topic_config)
    response = f"{answer} {response}".strip().replace("  ", " ")
    if response:
        state_utils.save_to_shared_memory(vars, cur_mode="smalltalk")
        state_utils.set_confidence(vars, confidence=CONF_DICT["WIKI_TOPIC"])
        if first_utt:
            state_utils.set_can_continue(vars, continue_flag=common_constants.MUST_CONTINUE)
        else:
            state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    else:
        state_utils.set_confidence(vars, confidence=CONF_DICT["UNDEFINED"])
        state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_NOT_CONTINUE)
    return response


def start_or_continue_facts(vars, topic_config):
    flag = False
    shared_memory = state_utils.get_shared_memory(vars)
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
            if cur_wikipedia_page or cur_wikihow_page and not isno:
                wikihow_page_content_list = memory.get("wikihow_content", [])
                wikipedia_page_content_list = memory.get("wikipedia_content", [])
                used_wikihow_nums = shared_memory.get("used_wikihow_nums", {}).get(cur_wikihow_page, [])
                used_wikipedia_nums = shared_memory.get("used_wikipedia_nums", {}).get(cur_wikipedia_page, [])
                logger.info(f"request, used_wikihow_nums {used_wikihow_nums} used_wikipedia_nums {used_wikipedia_nums}")
                logger.info(f"request, wikipedia_page_content_list {wikipedia_page_content_list} "
                            f"wikihow_page_content_list {wikihow_page_content_list}")
                if len(wikihow_page_content_list) > 0 and len(used_wikihow_nums) < len(wikihow_page_content_list):
                    flag = True
                if len(wikipedia_page_content_list) > 0 and len(used_wikipedia_nums) < len(wikipedia_page_content_list):
                    flag = True
    return flag


def facts_response(vars, topic_config):
    shared_memory = state_utils.get_shared_memory(vars)
    isyes = is_yes(state_utils.get_last_human_utterance(vars))
    response = ""
    cur_mode = shared_memory.get("cur_mode", "smalltalk")
    wikipedia_page = shared_memory.get("cur_wikipedia_page", "")
    wikihow_page = shared_memory.get("cur_wikihow_page", "")
    found_topic = shared_memory.get("special_topic", "")
    extract_and_save_entity(vars)
    extract_and_save_subtopic(vars)
    extract_and_save_wikipage(vars)
    if cur_mode == "smalltalk":
        if "triggers" in topic_config[found_topic]:
            triggers = topic_config[found_topic]["triggers"]
            entity_substr, entity_types, wikipedia_page, wikihow_page = find_trigger(vars, triggers)
        if not wikihow_page:
            wikihow_page = shared_memory.get("cur_wikihow_page", "")
        if wikihow_page:
            page_content = get_wikihow_content(wikihow_page)
            wikihow_page_content_list = preprocess_wikihow_page(page_content)
            memory["wikihow_content"] = wikihow_page_content_list
            state_utils.save_to_shared_memory(vars, cur_wikihow_page=wikihow_page)

        if wikipedia_page:
            page_content, _ = get_page_content(wikipedia_page)
            wikipedia_page_content_list = preprocess_wikipedia_page(entity_substr, entity_types, page_content)
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
        logger.info(f"response, wikipedia_page_content_list {wikipedia_page_content_list} "
                    f"wikihow_page_content_list {wikihow_page_content_list}")
        if wikihow_page_content_list:
            for num, fact in enumerate(wikihow_page_content_list):
                if num not in used_wikihow_nums:
                    response = fact
                    used_wikihow_nums.append(num)
                    used_wikihow_nums_dict[wikihow_page] = used_wikihow_nums
                    state_utils.save_to_shared_memory(vars, used_wikihow_nums=used_wikihow_nums_dict)
                    break
        if not response and wikipedia_page_content_list:
            for num, fact in enumerate(wikipedia_page_content_list):
                if num not in used_wikipedia_nums:
                    response = fact
                    used_wikipedia_nums.append(num)
                    used_wikipedia_nums_dict[wikipedia_page] = used_wikipedia_nums
                    state_utils.save_to_shared_memory(vars, used_wikipedia_nums=used_wikipedia_nums_dict)
                    break
        cur_mode = "facts"
        if len(wikihow_page_content_list) == len(used_wikihow_nums) \
                and len(wikipedia_page_content_list) == len(used_wikipedia_nums):
            cur_mode = "smalltalk"
            if len(wikihow_page_content_list) == len(used_wikihow_nums):
                state_utils.save_to_shared_memory(vars, cur_wikihow_page="")
                memory["wikihow_content"] = []
            if len(wikipedia_page_content_list) == len(used_wikipedia_nums):
                state_utils.save_to_shared_memory(vars, cur_wikipedia_page="")
                memory["wikipedia_content"] = []

    answer = answer_users_question(vars, topic_config)
    response = f"{answer} {response}".strip().replace("  ", " ")
    if response:
        state_utils.save_to_shared_memory(vars, cur_mode=cur_mode)
        state_utils.set_confidence(vars, confidence=CONF_DICT["WIKI_TOPIC"])
        if isyes:
            state_utils.set_can_continue(vars, continue_flag=common_constants.MUST_CONTINUE)
        else:
            state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    else:
        state_utils.set_confidence(vars, confidence=CONF_DICT["UNDEFINED"])
        state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_NOT_CONTINUE)
    return response
