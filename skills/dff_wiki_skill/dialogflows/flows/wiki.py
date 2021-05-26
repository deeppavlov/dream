import logging
import os
import random
import re
import requests
import en_core_web_sm
import nltk
import sentry_sdk

from deeppavlov import build_model

import common.constants as common_constants
import common.dialogflow_framework.stdm.dialogflow_extention as dialogflow_extention
import common.dialogflow_framework.utils.state as state_utils
from common.dialogflow_framework.utils.condition import if_was_prev_active
from common.universal_templates import COMPILE_NOT_WANT_TO_TALK_ABOUT_IT, COMPILE_LETS_TALK, \
    is_any_question_sentence_in_utterance
from common.utils import is_no, is_yes
from common.wiki_skill import used_types_dict
from common.wiki_skill import choose_title, find_all_titles, find_paragraph, find_all_paragraphs, delete_hyperlinks
from common.wiki_skill import find_entity_wp, find_entity_nounphr, if_switch_wiki_skill, continue_after_topic_skill
from common.wiki_skill import switch_wiki_skill_on_news, preprocess_news, if_must_switch
from common.wiki_skill import QUESTION_TEMPLATES, WIKI_BLACKLIST, CONF_DICT, NEWS_MORE
from common.news import get_news_about_topic

import dialogflows.scopes as scopes
from dialogflows.flows.wiki_states import State

sentry_sdk.init(os.getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

nlp = en_core_web_sm.load()

config_name = os.getenv("CONFIG")
text_qa_url = os.getenv("TEXT_QA_URL")

ANSWER_CONF_THRES = 0.95
GO_TO_MAIN_PAGE = True
ANIMAL_TYPES_SET = {"Q16521", "Q55983715", "Q38547", "Q39367", "Q43577"}

page_extractor = build_model(config_name, download=True)
whow_page_extractor = build_model("whow_page_extractor.json", download=True)


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


found_pages_dict = {}


def another_topic_question(vars, all_titles):
    flag = True
    shared_memory = state_utils.get_shared_memory(vars)
    curr_pages = shared_memory.get("curr_pages", [])
    found_entity_substr_list = shared_memory.get("found_entity_substr", [])
    used_titles = shared_memory.get("used_titles", [])
    annotations = state_utils.get_last_human_utterance(vars)["annotations"]
    nounphrases = annotations.get("cobot_nounphrases", [])
    for nounphr in nounphrases:
        if any([nounphr in curr_page.lower() for curr_page in curr_pages]) \
                or any([nounphr in entity_substr for entity_substr in found_entity_substr_list]) \
                or any([nounphr in title.lower() for title in used_titles]) \
                or any([nounphr in title.lower() for title in all_titles]):
            flag = False
    logger.info(f"another topic question {another_topic_question}")
    return flag


def if_wants_more(vars, all_titles):
    flag = False
    isyes = is_yes(state_utils.get_last_human_utterance(vars))
    isno = is_no(state_utils.get_last_human_utterance(vars))
    user_uttr = state_utils.get_last_human_utterance(vars)
    further = re.findall(r"(more|further|continue|follow)", user_uttr["text"], re.IGNORECASE)
    another_topic = another_topic_question(vars, all_titles)
    if isyes or (further and not isno):
        flag = True
    if another_topic and not isyes:
        flag = False
    if isno:
        flag = False
    logger.info(f"wants_more={flag}")
    return flag


def find_entity(vars, where_to_find="current"):
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    if where_to_find == "current":
        annotations = state_utils.get_last_human_utterance(vars)["annotations"]
        found_entity_substr, found_entity_id, found_entity_types, _ = find_entity_wp(annotations, bot_uttr)
        if not found_entity_substr:
            found_entity_substr, _ = find_entity_nounphr(annotations)
    else:
        all_user_uttr = vars["agent"]["dialog"]["human_utterances"]
        utt_num = len(all_user_uttr)
        found_entity_substr = ""
        found_entity_types = []
        found_entity_id = ""
        if utt_num > 1:
            for i in range(utt_num - 2, 0, -1):
                annotations = all_user_uttr[i]["annotations"]
                found_entity_substr, found_entity_id, found_entity_types, _ = find_entity_wp(annotations, bot_uttr)
                if not found_entity_substr:
                    found_entity_substr, _ = find_entity_nounphr(annotations)
                if found_entity_substr:
                    break
    logger.info(f"find_entity, substr {found_entity_substr} types {found_entity_types}")
    return found_entity_substr, found_entity_id, found_entity_types


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


def get_page_content(page_title):
    page_content = {}
    main_pages = {}
    try:
        if page_title:
            page_content_batch, main_pages_batch = page_extractor([[page_title]])
            if page_content_batch and page_content_batch[0]:
                page_content = page_content_batch[0][0]
                main_pages = main_pages_batch[0][0]
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)

    return page_content, main_pages


def get_wikihow_content(page_title):
    page_content = {}
    try:
        if page_title:
            page_content_batch = whow_page_extractor([[page_title]])
            if page_content_batch and page_content_batch[0]:
                page_content = page_content_batch[0][0]
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)

    return page_content


def get_page_info(vars, function_type, where_to_find="current"):
    shared_memory = state_utils.get_shared_memory(vars)
    curr_pages = shared_memory.get("curr_pages", [])
    found_entity_substr_list = shared_memory.get("found_entity_substr", [])
    prev_title = shared_memory.get("prev_title", "")
    prev_page_title = shared_memory.get("prev_page_title", "")
    used_titles = shared_memory.get("used_titles", [])
    found_entity_types_list = shared_memory.get("found_entity_types", [])
    started = shared_memory.get("start", False)
    was_prev_active = if_was_prev_active(vars)
    logger.info(f"started {started}")
    if function_type == "response" and curr_pages and found_entity_substr_list and found_entity_types_list:
        page_content, _ = get_page_content(curr_pages[-1])
        all_titles = find_all_titles([], page_content)
        wants_more = if_wants_more(vars, all_titles)
        logger.info(f"deleting, function_type {function_type} wants_more {wants_more}")
        if not wants_more:
            curr_pages.pop()
            found_entity_substr_list.pop()
            found_entity_types_list.pop()
    if not started or not was_prev_active:
        curr_pages = []
        found_entity_substr_list = []
        found_entity_types_list = []
        state_utils.save_to_shared_memory(vars, start=False)
    new_page = shared_memory.get("new_page", False)
    page_content_list = []
    main_pages_list = []
    if curr_pages:
        for page in curr_pages[-2:]:
            page_content, main_pages = get_page_content(page)
            page_content_list.append(page_content)
            main_pages_list.append(main_pages)
    else:
        found_entity_substr, _, found_entity_types = find_entity(vars, where_to_find)
        curr_page = get_page_title(vars, found_entity_substr)
        if curr_page:
            curr_pages.append(curr_page)
            found_entity_substr_list.append(found_entity_substr)
            found_entity_types_list.append(list(found_entity_types))
        for page in curr_pages[-2:]:
            page_content, main_pages = get_page_content(page)
            page_content_list.append(page_content)
            main_pages_list.append(main_pages)
    return found_entity_substr_list, prev_title, prev_page_title, found_entity_types_list, used_titles, curr_pages, \
        page_content_list, main_pages_list, new_page


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


def get_title_info(vars, found_entity_substr, found_entity_types, prev_title, used_titles, page_content):
    shared_memory = state_utils.get_shared_memory(vars)
    curr_pages = shared_memory.get("curr_pages", [])
    all_titles = find_all_titles([], page_content)
    titles_we_use = []
    for tp in found_entity_types:
        titles_we_use += list(titles_by_type.get(tp, {}).keys())
    titles_we_use += list(titles_by_entity_substr.get(found_entity_substr, {}).keys())

    logger.info(f"all_titles {all_titles}")
    chosen_title, chosen_page_title = choose_title(vars, all_titles, titles_we_use, prev_title, used_titles, curr_pages)
    return chosen_title, chosen_page_title


def make_facts_str(paragraphs):
    facts_str = ""
    mentions_list = []
    mention_pages_list = []
    paragraph = ""
    logger.info(f"paragraphs {paragraphs}")
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
    logger.info(f"mentions {mentions_list} mention_pages {mention_pages_list}")
    return facts_str, mentions_list, mention_pages_list


def make_question(chosen_title, titles_q, found_entity_substr, used_titles):
    if chosen_title in titles_q and titles_q[chosen_title]:
        question = titles_q[chosen_title].format(found_entity_substr)
    else:
        if len(used_titles) == 1:
            question_template = QUESTION_TEMPLATES[0]
        else:
            question_template = random.choice(QUESTION_TEMPLATES)
        if (found_entity_substr in chosen_title.lower() and question_template.endswith("of {}?")) \
                or " of " in chosen_title.lower():
            question_template = question_template.split(" of {}?")[0] + "?"
            question = question_template.format(chosen_title)
        else:
            question = question_template.format(chosen_title, found_entity_substr)
    question = question.replace(" of of ", " of ")
    return question


def make_response(vars, prev_page_title, page_content, question):
    mentions_list = []
    mention_pages_list = []
    facts_str = ""
    if prev_page_title:
        paragraphs = find_paragraph(page_content, prev_page_title)
        facts_str, mentions_list, mention_pages_list = make_facts_str(paragraphs)
    logger.info(f"facts_str {facts_str} question {question}")
    response = f"{facts_str} {question}"
    response = response.strip()
    state_utils.save_to_shared_memory(vars, mentions=mentions_list)
    state_utils.save_to_shared_memory(vars, mention_pages=mention_pages_list)
    return response


def save_wiki_vars(vars, found_entity_substr_list, curr_pages, prev_title, prev_page_title, used_titles,
                   found_entity_types_list, new_page):
    state_utils.save_to_shared_memory(vars, found_entity_substr=found_entity_substr_list)
    state_utils.save_to_shared_memory(vars, curr_pages=curr_pages)
    state_utils.save_to_shared_memory(vars, prev_title=prev_title)
    state_utils.save_to_shared_memory(vars, prev_page_title=prev_page_title)
    state_utils.save_to_shared_memory(vars, used_titles=used_titles)
    state_utils.save_to_shared_memory(vars, found_entity_types=list(found_entity_types_list))
    state_utils.save_to_shared_memory(vars, new_page=new_page)


def news_step_request(ngrams, vars):
    flag = False
    shared_memory = state_utils.get_shared_memory(vars)
    started_news = shared_memory.get("started_news", "")
    user_uttr = state_utils.get_last_human_utterance(vars)
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    isno = is_no(state_utils.get_last_human_utterance(vars))
    if_switch = switch_wiki_skill_on_news(user_uttr, bot_uttr)
    news_memory = shared_memory.get("news_memory", [])
    cur_news_title = shared_memory.get("news_title", "")
    found_not_used_content = False
    if cur_news_title:
        title_num = -1
        for n, elem in enumerate(news_memory):
            if elem["title"] == cur_news_title:
                for sentence_num, (sentence, used_sent) in enumerate(elem["content"]):
                    if not used_sent:
                        found_not_used_content = True
                title_num = n
        if not found_not_used_content and -1 < title_num < len(news_memory) - 1:
            found_not_used_content = True
    logger.info(f"news_step_request, started_news {started_news} if_switch {if_switch} "
                f"cur_news_title {cur_news_title} found_not_used_content {found_not_used_content}")

    if (not started_news and if_switch) or (started_news and cur_news_title and found_not_used_content):
        flag = True
    if isno or "?" in user_uttr["text"]:
        flag = False
    logger.info(f"news_step_request={flag}")
    return flag


def news_step_response(vars):
    shared_memory = state_utils.get_shared_memory(vars)
    started_news = shared_memory.get("started_news", "")
    found_entity_substr, _, found_entity_types = find_entity(vars, "current")
    curr_page = get_page_title(vars, found_entity_substr)
    if not started_news and found_entity_substr and curr_page:
        state_utils.save_to_shared_memory(vars, found_entity_substr=[found_entity_substr])
        state_utils.save_to_shared_memory(vars, curr_pages=[curr_page])
        state_utils.save_to_shared_memory(vars, found_entity_types=[list(found_entity_types)])
    user_uttr = state_utils.get_last_human_utterance(vars)
    annotations = user_uttr["annotations"]
    nounphrases = annotations.get("cobot_entities", {}).get("labelled_entities", [])
    nounphrases = [nounphr["text"] for nounphr in nounphrases]
    logger.info(f"news_step_response {nounphrases}")
    response = ""
    news_entity = ""
    if not started_news:
        for nounphr in nounphrases:
            result_news = []
            try:
                result_news = get_news_about_topic(nounphr, "http://news-api-annotator:8112/respond",
                                                   return_list_of_news=True, timeout_value=1.3)
            except Exception as e:
                sentry_sdk.capture_exception(e)
                logger.exception(e)
            if not result_news:
                result_news = annotations.get("news_api_annotator", [])
            if result_news:
                processed_news = preprocess_news(result_news)
                logger.info(f"processed_news {processed_news[:2]}")
                news_entity = nounphr
                state_utils.save_to_shared_memory(vars, news_entity=news_entity)
                state_utils.save_to_shared_memory(vars, news_memory=processed_news)
                break
    new_title = ""
    found_content = ""
    news_memory = shared_memory.get("news_memory", [])
    if not started_news:
        if news_entity and news_memory:
            new_title = news_memory[0]["title"]
            state_utils.save_to_shared_memory(vars, news_title=new_title)
    else:
        cur_news_title = shared_memory.get("news_title")
        title_num = -1
        found_sentence_num = -1
        for n, elem in enumerate(news_memory):
            if elem["title"] == cur_news_title:
                for sentence_num, (sentence, used_sent) in enumerate(elem["content"]):
                    if not used_sent:
                        found_content = sentence
                        found_sentence_num = sentence_num
                        news_memory[n]["content"][sentence_num][1] = True
                        break
                title_num = n
        if found_sentence_num == len(news_memory[title_num]["content"]) - 1 and -1 < title_num < len(news_memory) - 1:
            new_title = news_memory[title_num + 1]["title"]
            state_utils.save_to_shared_memory(vars, news_title=new_title)
        if not found_content and -1 < title_num < len(news_memory) - 1:
            title = news_memory[title_num + 1]["title"]
            found_content = news_memory[title_num + 1]["content"][0][0]
            news_memory[title_num + 1]["content"][0][1] = True
            state_utils.save_to_shared_memory(vars, news_title=title)
    state_utils.save_to_shared_memory(vars, news_memory=news_memory)
    logger.info(f"news_step_response found_content {found_content} new_title {new_title} news_entity {news_entity}")

    if not started_news:
        response = f"Talking about {news_entity}. I've recently heard that {new_title}. Do you want to hear more?"
    elif found_content:
        if new_title:
            response = f"{found_content} I also heard that {new_title}. Would you like to hear more?"
        else:
            continue_phrase = random.choice(NEWS_MORE)
            response = f"In details: {found_content} {continue_phrase}"

    if response:
        if started_news:
            state_utils.set_confidence(vars, confidence=CONF_DICT["WIKI_TOPIC"])
            state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
        else:
            state_utils.set_confidence(vars, confidence=CONF_DICT["IN_SCENARIO"])
            state_utils.set_can_continue(vars, continue_flag=common_constants.MUST_CONTINUE)
            state_utils.save_to_shared_memory(vars, started_news=True)
    else:
        state_utils.set_confidence(vars, confidence=CONF_DICT["UNDEFINED"])
        state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_NOT_CONTINUE)
    return response


def intro_question_request(ngrams, vars):
    flag = False
    shared_memory = state_utils.get_shared_memory(vars)
    curr_pages = shared_memory.get("curr_pages", [])
    if not curr_pages:
        found_entity_substr, _, found_entity_types = find_entity(vars, "current")
        if found_entity_substr and found_entity_substr in questions_by_entity_substr:
            flag = True
    logger.info(f"intro_question_request={flag}")
    return flag


def wikihow_question_request(ngrams, vars):
    flag = False
    shared_memory = state_utils.get_shared_memory(vars)
    curr_pages = shared_memory.get("curr_pages", [])
    if not curr_pages:
        found_entity_substr, _, found_entity_types = find_entity(vars, "current")
        if found_entity_substr and found_entity_substr in wikihowq_by_substr:
            flag = True
    logger.info(f"wikihow_question_request={flag}")
    return flag


def wikihow_step_request(ngrams, vars):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    isyes = is_yes(state_utils.get_last_human_utterance(vars))
    shared_memory = state_utils.get_shared_memory(vars)
    wikihow_article = shared_memory.get("wikihow_article", "")
    prev_wikihow_title = shared_memory.get("prev_wikihow_title", "")
    used_wikihow_titles = set(shared_memory.get("used_wikihow_titles", []))
    logger.info(f"wikihow_step_request, prev_wikihow_title {prev_wikihow_title} used_wikihow_titles "
                f"{used_wikihow_titles}")
    found_title = ""
    if wikihow_article:
        article_content = get_wikihow_content(wikihow_article)
        if article_content:
            all_page_titles = article_content.keys()
            for title in all_page_titles:
                if title not in used_wikihow_titles:
                    found_title = title
                    break
    further = re.findall(r"(more|further|continue|follow)", user_uttr["text"], re.IGNORECASE)
    if found_title or prev_wikihow_title:
        flag = True
    if prev_wikihow_title and not (isyes or further):
        flag = False
    logger.info(f"wikihow_step_request={flag}")
    return flag


def start_talk_request(ngrams, vars):
    flag = False
    dialog = vars["agent"]["dialog"]
    chosen_title, chosen_page_title = "", ""
    all_titles = []
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    prev_skill = bot_uttr.get("active_skill", "")
    if prev_skill != "dff_wiki_skill":
        found_entity_substr, found_entity_id, found_entity_types, found_page_title, _ = \
            continue_after_topic_skill(dialog)
        if found_entity_substr and found_page_title:
            page_content, _ = get_page_content(found_page_title)
            chosen_title, chosen_page_title = get_title_info(vars, found_entity_substr, found_entity_types, "", [],
                                                             page_content)
            _, _, all_titles = get_titles(found_entity_substr, found_entity_types, page_content)
        logger.info(f"start_talk_request, found_entity_substr {found_entity_substr} found_entity_id {found_entity_id} "
                    f"found_entity_types {found_entity_types} found_page_title {found_page_title} "
                    f"chosen_title {chosen_title}")
        user_uttr = state_utils.get_last_human_utterance(vars)
        isno = is_no(state_utils.get_last_human_utterance(vars))
        if chosen_title:
            flag = True
        if (user_uttr["text"].endswith("?") and another_topic_question(vars, all_titles)) or isno:
            flag = False
    logger.info(f"start_talk_request={flag}")
    return flag


def more_details_request(ngrams, vars):
    flag = False
    shared_memory = state_utils.get_shared_memory(vars)
    mentions_list = shared_memory.get("mentions", [])
    user_uttr = state_utils.get_last_human_utterance(vars)
    annotations = user_uttr["annotations"]
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    bot_more_details = "more details" in bot_uttr["text"]
    user_more_details = re.findall(COMPILE_LETS_TALK, user_uttr["text"])
    isyes = is_yes(state_utils.get_last_human_utterance(vars))
    nounphrases = annotations.get("cobot_nounphrases", [])
    inters = set(nounphrases).intersection(set(mentions_list))
    started = shared_memory.get("start", False)
    if ((user_more_details and inters) or (bot_more_details and isyes)) and started:
        flag = True
    logger.info(f"more_details_request={flag}")
    return flag


def factoid_q_request(ngrams, vars):
    flag = False
    shared_memory = state_utils.get_shared_memory(vars)
    user_uttr = state_utils.get_last_human_utterance(vars)
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    user_more_details = re.findall(COMPILE_LETS_TALK, user_uttr["text"])
    user_annotations = user_uttr["annotations"]
    is_factoid = False
    factoid_cl = user_annotations.get("factoid_classification", {})
    if factoid_cl and factoid_cl["factoid"] > factoid_cl["conversational"]:
        is_factoid = True
    bot_text = bot_uttr["text"].lower()
    sentences = nltk.sent_tokenize(bot_text)
    if len(sentences) > 1:
        sentences = [sentence for sentence in sentences if not sentence.endswith("?")]
    bot_text = " ".join(sentences)
    nounphrases = user_annotations.get("cobot_nounphrases", [])
    found_nounphr = any([nounphrase in bot_text for nounphrase in nounphrases])
    logger.info(f"factoid_q_request, is_factoid {is_factoid} user_more_details {user_more_details} "
                f"nounphrases {nounphrases} bot_text {bot_text}")
    started = shared_memory.get("start", False)
    if is_factoid and not user_more_details and found_nounphr and started:
        flag = True
    logger.info(f"factoid_q_request={flag}")
    return flag


def tell_fact_request(ngrams, vars):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    found_entity_substr_list, prev_title, prev_page_title, found_entity_types_list, used_titles, _, page_content_list, \
        main_pages_list, page = get_page_info(vars, "request")
    logger.info(f"request, found_entity_substr {found_entity_substr_list} prev_title {prev_title} "
                f"found_entity_types {found_entity_types_list} used_titles {used_titles}")
    shared_memory = state_utils.get_shared_memory(vars)
    started = shared_memory.get("start", False)
    shared_state = vars["agent"]["dff_shared_state"]
    logger.info(f"shared_state {shared_state}")
    if found_entity_substr_list and found_entity_types_list and page_content_list:
        chosen_title, chosen_page_title = get_title_info(vars, found_entity_substr_list[-1],
                                                         found_entity_types_list[-1], prev_title, used_titles,
                                                         page_content_list[-1])
        _, _, all_titles = get_titles(found_entity_substr_list[-1], found_entity_types_list[-1], page_content_list[-1])
        logger.info(f"request, chosen_title {chosen_title} chosen_page_title {chosen_page_title}")
        wants_more = if_wants_more(vars, all_titles)
        not_want = re.findall(COMPILE_NOT_WANT_TO_TALK_ABOUT_IT, user_uttr["text"])

        if (chosen_title or prev_title) and ((wants_more and not not_want) or not started
                                             or len(found_entity_substr_list) > 1):
            flag = True
        if user_uttr["text"].endswith("?") and another_topic_question(vars, all_titles):
            flag = False
    logger.info(f"tell_fact_request={flag}")
    return flag


def intro_question_response(vars):
    response = ""
    shared_memory = state_utils.get_shared_memory(vars)
    curr_pages = shared_memory.get("curr_pages", [])
    if not curr_pages:
        found_entity_substr, _, found_entity_types = find_entity(vars, "current")
        if found_entity_substr and found_entity_substr in questions_by_entity_substr:
            response = questions_by_entity_substr[found_entity_substr]
    if response:
        state_utils.save_to_shared_memory(vars, start=True)
        state_utils.set_confidence(vars, confidence=CONF_DICT["WIKI_TOPIC"])
        state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_PROMPT)
    else:
        state_utils.set_confidence(vars, confidence=CONF_DICT["UNDEFINED"])
        state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_NOT_CONTINUE)
    return response


def wikihow_question_response(vars):
    response = ""
    shared_memory = state_utils.get_shared_memory(vars)
    curr_pages = shared_memory.get("curr_pages", [])
    if not curr_pages:
        found_entity_substr, _, found_entity_types = find_entity(vars, "current")
        if found_entity_substr and found_entity_substr in wikihowq_by_substr:
            wikihow_questions = wikihowq_by_substr[found_entity_substr]
            wikihow_articles = list(wikihow_questions.keys())
            chosen_article = random.choice(wikihow_articles)
            article_content = get_wikihow_content(chosen_article)
            if article_content:
                all_page_titles = article_content.keys()
                found_title = ""
                for title in all_page_titles:
                    if title != "intro":
                        found_title = title
                        break
                if found_title:
                    state_utils.save_to_shared_memory(vars, prev_wikihow_title=found_title)
                    used_wikihow_titles = [found_title]
                    state_utils.save_to_shared_memory(vars, used_wikihow_titles=used_wikihow_titles)
            response = wikihow_questions[chosen_article]
            if not response:
                response = f"Would you like to know how to {chosen_article.replace('-', ' ').lower()}?"
            logger.info(f"wikihow_question_response, chosen_article {chosen_article} response {response}")
            state_utils.save_to_shared_memory(vars, wikihow_article=chosen_article)
    if response:
        state_utils.save_to_shared_memory(vars, start=True)
        state_utils.set_confidence(vars, confidence=CONF_DICT["WIKI_TOPIC"])
        state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_PROMPT)
    else:
        state_utils.set_confidence(vars, confidence=CONF_DICT["UNDEFINED"])
        state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_NOT_CONTINUE)
    return response


def wikihow_step_response(vars):
    shared_memory = state_utils.get_shared_memory(vars)
    wikihow_article = shared_memory.get("wikihow_article", "")
    prev_wikihow_title = shared_memory.get("prev_wikihow_title", "")
    used_wikihow_titles = shared_memory.get("used_wikihow_titles", [])
    found_title = ""
    facts_str = ""
    question = ""
    if wikihow_article:
        article_content = get_wikihow_content(wikihow_article)
        if article_content:
            all_page_titles = article_content.keys()
            for title in all_page_titles:
                if title not in used_wikihow_titles and title != "intro":
                    found_title = title
                    break
            if prev_wikihow_title:
                paragraphs = article_content[prev_wikihow_title]
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
                    logger.info(f"wikihow_step_response, sentences_list {sentences_list} facts_str {facts_str}")
            if found_title:
                question = f"Would you like to know about {found_title.lower()}?"
    logger.info(f"wikihow_step_response found_title {found_title} prev_wikihow_title {prev_wikihow_title}")
    response = f"{facts_str} {question}"
    response = response.strip()
    if found_title:
        state_utils.save_to_shared_memory(vars, prev_wikihow_title=found_title)
        used_wikihow_titles.append(found_title)
        state_utils.save_to_shared_memory(vars, used_wikihow_titles=used_wikihow_titles)
    if response:
        state_utils.set_confidence(vars, confidence=CONF_DICT["IN_SCENARIO"])
        state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    else:
        state_utils.set_confidence(vars, confidence=CONF_DICT["UNDEFINED"])
        state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_NOT_CONTINUE)

    return response


def start_talk_response(vars):
    used_titles = []
    dialog = vars["agent"]["dialog"]
    found_entity_substr, found_entity_id, found_entity_types, found_page_title, _ = continue_after_topic_skill(dialog)
    page_content, _ = get_page_content(found_page_title)
    found_entity_substr_list = [found_entity_substr]
    found_entity_types_list = [list(found_entity_types)]
    curr_pages = [found_page_title]
    chosen_title, chosen_page_title = get_title_info(vars, found_entity_substr, found_entity_types, "", [],
                                                     page_content)
    titles_q, titles_we_use, all_titles = get_titles(found_entity_substr, found_entity_types, page_content)
    question = make_question(chosen_title, titles_q, found_entity_substr, [])
    chosen_title, chosen_page_title = choose_title(vars, all_titles, titles_we_use, "", [], curr_pages)
    response = question.strip()
    if chosen_title:
        used_titles.append(chosen_title)
    save_wiki_vars(vars, found_entity_substr_list, curr_pages, chosen_title, chosen_page_title, used_titles,
                   found_entity_types_list, False)
    cross_link = state_utils.get_cross_link(vars, service_name="dff_wiki_skill")
    from_skill = cross_link.get("from_service", "")
    if from_skill:
        state_utils.save_to_shared_memory(vars, interrupted_skill=from_skill)
    if response:
        state_utils.save_to_shared_memory(vars, start=True)
        state_utils.set_confidence(vars, confidence=CONF_DICT["ENTITY_IN_HISTORY"])
        if from_skill:
            state_utils.set_can_continue(vars, continue_flag=common_constants.MUST_CONTINUE)
        else:
            state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_PROMPT)
    else:
        state_utils.set_confidence(vars, confidence=CONF_DICT["UNDEFINED"])
        state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_NOT_CONTINUE)
    return response


def more_details_response(vars):
    shared_memory = state_utils.get_shared_memory(vars)
    used_titles = shared_memory.get("used_titles", [])
    mentions_list = shared_memory.get("mentions", [])
    curr_pages = shared_memory.get("curr_pages", [])
    mention_pages_list = shared_memory.get("mention_pages", [])
    mentions_dict = {}
    for mention, mention_page in zip(mentions_list, mention_pages_list):
        mentions_dict[mention] = mention_page
    user_uttr = state_utils.get_last_human_utterance(vars)
    annotations = user_uttr["annotations"]
    nounphrases = annotations.get("cobot_nounphrases", [])
    inters = list(set(nounphrases).intersection(set(mentions_list)))
    found_entity_substr_list = []
    found_entity_substr = inters[0]
    found_entity_substr_list.append(found_entity_substr)
    found_entity_types = []
    new_page = False
    curr_page = mentions_dict[found_entity_substr]
    if curr_page:
        curr_pages.append(curr_page)
        new_page = True
    logger.info(f"more_details_response, found_entity_substr {found_entity_substr} curr_pages {curr_pages}")
    page_content, main_pages = get_page_content(curr_page)
    first_pars = page_content["first_par"]
    facts_str, new_mentions_list, new_mention_pages_list = make_facts_str(first_pars)
    titles_q, titles_we_use, all_titles = get_titles(found_entity_substr, found_entity_types, page_content)
    if not titles_we_use:
        titles_we_use = list(set(page_content.keys()).difference({"first_par"}))
    logger.info(f"all_titles {all_titles} titles_q {titles_q} titles_we_use {titles_we_use}")
    chosen_title, chosen_page_title = choose_title(vars, all_titles, titles_we_use, "", [], curr_pages)
    question = make_question(chosen_title, titles_q, found_entity_substr, [])
    response = f"{facts_str} {question}"
    response = response.strip()
    if chosen_title:
        used_titles.append(chosen_title)
    save_wiki_vars(vars, found_entity_substr_list, curr_pages, chosen_title, chosen_page_title, used_titles, [[]],
                   new_page)
    if response:
        state_utils.set_confidence(vars, confidence=CONF_DICT["IN_SCENARIO"])
        state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    else:
        state_utils.set_confidence(vars, confidence=CONF_DICT["UNDEFINED"])
        state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_NOT_CONTINUE)
    return response


def factoid_q_response(vars):
    paragraphs = []
    shared_memory = state_utils.get_shared_memory(vars)
    prev_page_title = shared_memory.get("prev_page_title", "")
    mentions = shared_memory.get("mentions", [])
    mention_pages = shared_memory.get("mention_pages", [])
    curr_pages = shared_memory.get("curr_pages", [])
    new_page = shared_memory.get("new_page", False)
    if new_page and len(curr_pages) > 1:
        cur_page_content, cur_main_pages = get_page_content(curr_pages[-2])
        cur_paragraphs = find_paragraph(cur_page_content, prev_page_title)
        paragraphs += cur_paragraphs
        new_page_content, new_main_pages = get_page_content(curr_pages[-1])
        new_paragraphs = find_all_paragraphs(new_page_content, [])
        paragraphs += new_paragraphs
    else:
        cur_page_content, cur_main_pages = get_page_content(curr_pages[-1])
        cur_paragraphs = find_paragraph(cur_page_content, prev_page_title)
        paragraphs += cur_paragraphs
    logger.info(f"curr_pages {curr_pages} prev_page_title {prev_page_title}")

    mentions_dict = {}
    for mention, page in zip(mentions, mention_pages):
        mentions_dict[mention] = page
    user_uttr = state_utils.get_last_human_utterance(vars)
    user_annotations = user_uttr["annotations"]
    nounphrases = user_annotations.get("cobot_nounphrases", [])
    used_pages = []
    logger.info(f"nounphrases {nounphrases} mentions {mentions}")
    for nounphrase in nounphrases:
        for mention in mentions:
            if nounphrase in mention or mention in nounphrase:
                used_pages.append(mentions_dict[mention])
                break

    for page in used_pages:
        page_content, main_pages = get_page_content(page)
        paragraphs = find_all_paragraphs(page_content, paragraphs)

    clean_paragraphs = []
    for paragraph in paragraphs:
        clean_paragraph, _, _ = delete_hyperlinks(paragraph)
        clean_paragraphs.append(clean_paragraph)

    logger.info(f"clean_paragraphs {clean_paragraphs}")
    logger.info(f"factoid_q_response, used_pages {used_pages}")
    found_answer_sentence = ""
    try:
        res = requests.post(text_qa_url, json={"question_raw": [user_uttr["text"]], "top_facts": [clean_paragraphs]},
                            timeout=1.0)
        if res.status_code == 200:
            text_qa_output = res.json()[0]
            logger.info(f"text_qa_output {text_qa_output}")
            answer, conf, _, answer_sentence = text_qa_output
            if conf > ANSWER_CONF_THRES:
                found_answer_sentence = answer_sentence
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)

    logger.info(f"found_answer_sentence {found_answer_sentence}")
    response = found_answer_sentence

    return response


def tell_fact_response(vars):
    shared_memory = state_utils.get_shared_memory(vars)
    user_uttr = state_utils.get_last_human_utterance(vars)
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    found_entity_substr_list, prev_title, prev_page_title, found_entity_types_list, used_titles, curr_pages, \
        page_content_list, main_pages_list, new_page = get_page_info(vars, "response")
    logger.info(f"tell_fact_response, found_entity_substr {found_entity_substr_list} prev_title {prev_title} "
                f"prev_page_title {prev_page_title} found_entity_types {found_entity_types_list} used_titles "
                f"{used_titles} curr_pages {curr_pages}")
    titles_q, titles_we_use, all_titles = {}, [], []
    if found_entity_substr_list and found_entity_types_list and page_content_list:
        titles_q, titles_we_use, all_titles = get_titles(found_entity_substr_list[-1], found_entity_types_list[-1],
                                                         page_content_list[-1])
    logger.info(f"all_titles {all_titles} titles_q {titles_q} titles_we_use {titles_we_use}")
    chosen_title, chosen_page_title = choose_title(vars, all_titles, titles_we_use, prev_title, used_titles,
                                                   curr_pages)
    logger.info(f"chosen_title {chosen_title} main_pages {main_pages_list}")
    if chosen_title:
        new_page = False
        if GO_TO_MAIN_PAGE and not any([set(found_entity_types).intersection(ANIMAL_TYPES_SET) for
                                        found_entity_types in found_entity_types_list]):
            chosen_main_pages = main_pages_list[-1].get(chosen_page_title, [])
            if chosen_main_pages:
                chosen_main_page = random.choice(chosen_main_pages)
                curr_pages.append(chosen_main_page)
                new_page = True
                found_entity_substr_list.append(chosen_main_page.lower())
                found_entity_types_list.append([])
        used_titles.append(chosen_title)
        save_wiki_vars(vars, found_entity_substr_list, curr_pages, chosen_title, chosen_page_title, used_titles,
                       found_entity_types_list, new_page)
    else:
        save_wiki_vars(vars, [], [], "", "", [], [], False)

    question = ""
    if found_entity_substr_list and chosen_title:
        question = make_question(chosen_title, titles_q, found_entity_substr_list[-1], used_titles)
    if new_page:
        if len(page_content_list) == 1:
            response = make_response(vars, prev_page_title, page_content_list[-1], question)
        else:
            response = make_response(vars, prev_page_title, page_content_list[-2], question)
    else:
        response = make_response(vars, prev_page_title, page_content_list[-1], question)
    started = shared_memory.get("start", False)
    has_q = is_any_question_sentence_in_utterance(user_uttr) and not re.findall(r"(let's|let us)", user_uttr["text"])
    _, conf_type = if_switch_wiki_skill(user_uttr, bot_uttr)

    cross_link = state_utils.get_cross_link(vars, service_name="dff_wiki_skill")
    from_skill = cross_link.get("from_service", "")
    if from_skill:
        state_utils.save_to_shared_memory(vars, interrupted_skill=from_skill)

    interrupted_skill = shared_memory.get("interrupted_skill", "")
    logger.info(f"interrupted_skill {interrupted_skill}")
    if interrupted_skill:
        state_utils.set_cross_link(vars, to_service_name=interrupted_skill, from_service_name="dff_wiki_skill")

    must_switch = if_must_switch(user_uttr, bot_uttr)
    if response:
        if not started and has_q:
            state_utils.set_confidence(vars, confidence=CONF_DICT["USER_QUESTION_IN_BEGIN"])
            state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_PROMPT)
        else:
            if not started:
                state_utils.set_confidence(vars, confidence=CONF_DICT[conf_type])
            else:
                state_utils.set_confidence(vars, confidence=CONF_DICT["IN_SCENARIO"])
            if interrupted_skill or must_switch:
                state_utils.set_can_continue(vars, continue_flag=common_constants.MUST_CONTINUE)
            else:
                state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)

        state_utils.save_to_shared_memory(vars, start=True)
    else:
        state_utils.set_confidence(vars, confidence=CONF_DICT["UNDEFINED"])
        state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_NOT_CONTINUE)
    return response


def error_response(vars):
    state_utils.save_to_shared_memory(vars, start=False)
    save_wiki_vars(vars, [], [], "", "", [], [], False)
    state_utils.save_to_shared_memory(vars, wikihow_article="")
    state_utils.save_to_shared_memory(vars, prev_wikihow_title="")
    state_utils.save_to_shared_memory(vars, used_wikihow_titles=[])
    state_utils.save_to_shared_memory(vars, interrupted_skill="")
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_NOT_CONTINUE)
    state_utils.set_confidence(vars, 0)
    return ""


simplified_dialog_flow = dialogflow_extention.DFEasyFilling(State.USR_START)

simplified_dialog_flow.add_user_serial_transitions(
    State.USR_START,
    {
        State.SYS_NEWS_STEP: news_step_request,
        State.SYS_WIKIHOW_Q: wikihow_question_request,
        State.SYS_INTRO_Q: intro_question_request,
        State.SYS_FACTOID_Q: factoid_q_request,
        State.SYS_TELL_FACT: tell_fact_request,
        State.SYS_START_TALK: start_talk_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    State.USR_INTRO_Q,
    {
        State.SYS_TELL_FACT: tell_fact_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    State.USR_WIKIHOW_Q,
    {
        State.SYS_WIKIHOW_STEP: wikihow_step_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    State.USR_WIKIHOW_STEP,
    {
        State.SYS_WIKIHOW_STEP: wikihow_step_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    State.USR_MORE_DETAILED,
    {
        State.SYS_TELL_FACT: tell_fact_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    State.USR_START_TALK,
    {
        State.SYS_START_TALK: start_talk_request,
        State.SYS_FACTOID_Q: factoid_q_request,
        State.SYS_TELL_FACT: tell_fact_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    State.USR_TELL_FACT,
    {
        State.SYS_FACTOID_Q: factoid_q_request,
        State.SYS_MORE_DETAILED: more_details_request,
        State.SYS_TELL_FACT: tell_fact_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    State.USR_NEWS_STEP,
    {
        State.SYS_NEWS_STEP: news_step_request,
        State.SYS_TELL_FACT: tell_fact_request,
    },
)

simplified_dialog_flow.add_system_transition(State.SYS_WIKIHOW_Q, State.USR_WIKIHOW_Q,
                                             wikihow_question_response, )
simplified_dialog_flow.add_system_transition(State.SYS_WIKIHOW_STEP, State.USR_WIKIHOW_STEP,
                                             wikihow_step_response, )
simplified_dialog_flow.add_system_transition(State.SYS_INTRO_Q, State.USR_INTRO_Q, intro_question_response, )
simplified_dialog_flow.add_system_transition(State.SYS_TELL_FACT, State.USR_TELL_FACT, tell_fact_response, )
simplified_dialog_flow.add_system_transition(State.SYS_FACTOID_Q, State.USR_FACTOID_Q, factoid_q_response, )
simplified_dialog_flow.add_system_transition(State.SYS_MORE_DETAILED, State.USR_MORE_DETAILED,
                                             more_details_response, )
simplified_dialog_flow.add_system_transition(State.SYS_START_TALK, State.USR_START_TALK, start_talk_response, )
simplified_dialog_flow.add_system_transition(State.SYS_NEWS_STEP, State.USR_NEWS_STEP, news_step_response, )
simplified_dialog_flow.add_system_transition(State.SYS_ERR, (scopes.MAIN, scopes.State.USR_ROOT), error_response, )

simplified_dialog_flow.set_error_successor(State.USR_START, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.SYS_TELL_FACT, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.USR_TELL_FACT, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.SYS_INTRO_Q, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.USR_INTRO_Q, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.SYS_WIKIHOW_Q, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.USR_WIKIHOW_Q, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.SYS_WIKIHOW_STEP, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.USR_WIKIHOW_STEP, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.SYS_START_TALK, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.USR_START_TALK, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.SYS_MORE_DETAILED, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.USR_MORE_DETAILED, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.SYS_FACTOID_Q, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.USR_FACTOID_Q, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.SYS_NEWS_STEP, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.USR_NEWS_STEP, State.SYS_ERR)

dialogflow = simplified_dialog_flow.get_dialogflow()
