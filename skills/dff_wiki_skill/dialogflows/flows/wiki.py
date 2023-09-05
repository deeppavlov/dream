import json
import logging
import os
import random
import re
import requests
import en_core_web_sm
import nltk
import sentry_sdk

import common.constants as common_constants
from dff import dialogflow_extension
import common.dialogflow_framework.utils.state as state_utils
from common.utils import is_no, is_yes
from common.universal_templates import COMPILE_NOT_WANT_TO_TALK_ABOUT_IT, COMPILE_LETS_TALK
from common.wiki_skill import choose_title, find_paragraph, find_all_paragraphs, delete_hyperlinks
from common.wiki_skill import if_switch_wiki_skill, continue_after_topic_skill
from common.wiki_skill import switch_wiki_skill_on_news, preprocess_news, if_must_switch
from common.wiki_skill import CONF_DICT, NEWS_MORE
from common.insert_scenario import (
    get_page_content,
    get_wikihow_content,
    get_page_title,
    make_facts_str,
    get_titles,
    questions_by_entity_substr,
    wikihowq_by_substr,
    preprocess_wikipedia_page,
    preprocess_wikihow_page,
)
from common.insert_scenario import (
    start_or_continue_scenario,
    smalltalk_response,
    start_or_continue_facts,
    facts_response,
    delete_topic_info,
)
from common.news import get_news_about_topic
from common.wiki_skill_scenarios import topic_config

import dialogflows.scopes as scopes
from dialogflows.flows.wiki_states import State
from dialogflows.flows.wiki_utils import (
    find_entity,
    get_title_info,
    another_topic_question,
    save_wiki_vars,
    make_question,
)

sentry_sdk.init(os.getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)

nlp = en_core_web_sm.load()

config_name = os.getenv("CONFIG")
text_qa_url = os.getenv("TEXT_QA_URL")

ANSWER_CONF_THRES = 0.95
GO_TO_MAIN_PAGE = True
ANIMAL_TYPES_SET = {"Q16521", "Q55983715", "Q38547", "Q39367", "Q43577"}

found_pages_dict = {}
facts_memory = {}

with open("wikipedia_cache.json", "r") as fl:
    wikipedia_cache = json.load(fl)

with open("wikihow_cache.json", "r") as fl:
    wikihow_cache = json.load(fl)


def special_topic_request(ngrams, vars):
    flag = start_or_continue_scenario(vars, topic_config)
    logger.info(f"special_topic_request={flag}")
    return flag


def special_topic_response(vars):
    response = smalltalk_response(vars, topic_config)
    return response


def special_topic_facts_request(ngrams, vars):
    flag = start_or_continue_facts(vars, topic_config)
    logger.info(f"special_topic_facts_request={flag}")
    return flag


def special_topic_facts_response(vars):
    response = facts_response(vars, topic_config, wikihow_cache, wikipedia_cache)
    return response


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
    logger.info(
        f"news_step_request, started_news {started_news} if_switch {if_switch} "
        f"cur_news_title {cur_news_title} found_not_used_content {found_not_used_content}"
    )

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
                result_news = get_news_about_topic(
                    nounphr, "http://news-api-annotator:8112/respond", return_list_of_news=True, timeout_value=1.3
                )
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

    if not started_news and news_entity and new_title:
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
    logger.info(
        f"wikihow_step_request, prev_wikihow_title {prev_wikihow_title} used_wikihow_titles " f"{used_wikihow_titles}"
    )
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
        found_entity_substr, found_entity_id, found_entity_types, found_page_title, _ = continue_after_topic_skill(
            dialog
        )
        if found_entity_substr and found_page_title:
            page_content, _ = get_page_content(found_page_title)
            chosen_title, chosen_page_title = get_title_info(
                vars, found_entity_substr, found_entity_types, "", [], page_content
            )
            _, _, all_titles = get_titles(found_entity_substr, found_entity_types, page_content)
        logger.info(
            f"start_talk_request, found_entity_substr {found_entity_substr} found_entity_id {found_entity_id} "
            f"found_entity_types {found_entity_types} found_page_title {found_page_title} "
            f"chosen_title {chosen_title}"
        )
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
    nounphrases = annotations.get("spacy_nounphrases", [])
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
    nounphrases = user_annotations.get("spacy_nounphrases", [])
    found_nounphr = any([nounphrase in bot_text for nounphrase in nounphrases])
    logger.info(
        f"factoid_q_request, is_factoid {is_factoid} user_more_details {user_more_details} "
        f"nounphrases {nounphrases} bot_text {bot_text}"
    )
    started = shared_memory.get("start", False)
    if is_factoid and not user_more_details and found_nounphr and started:
        flag = True
    logger.info(f"factoid_q_request={flag}")
    return flag


def tell_fact_request(ngrams, vars):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    isno = is_no(state_utils.get_last_human_utterance(vars))
    shared_memory = state_utils.get_shared_memory(vars)
    wikipedia_page = shared_memory.get("cur_wikipedia_page", "")
    wikihow_page = shared_memory.get("cur_wikihow_page", "")
    if "wikihow_content" in facts_memory and facts_memory["wikihow_content"]:
        used_wikihow_nums = shared_memory.get("used_wikihow_nums", {}).get(wikihow_page, [])
        if len(facts_memory["wikihow_content"]) > len(used_wikihow_nums):
            flag = True
    elif "wikipedia_content" in facts_memory and facts_memory["wikipedia_content"]:
        used_wikipedia_nums = shared_memory.get("used_wikipedia_nums", {}).get(wikipedia_page, [])
        if len(facts_memory["wikipedia_content"]) > len(used_wikipedia_nums):
            flag = True
    else:
        found_entity_substr, _, found_entity_types = find_entity(vars, "current")
        logger.info(f"request, found_entity_substr {found_entity_substr} found_entity_types {found_entity_types}")
        curr_page = get_page_title(vars, found_entity_substr)
        wikihow_articles = []
        if found_entity_substr in wikihowq_by_substr:
            wikihow_questions = wikihowq_by_substr[found_entity_substr]
            wikihow_articles = list(wikihow_questions.keys())
        if curr_page or wikihow_articles:
            flag = True

    not_want = re.findall(COMPILE_NOT_WANT_TO_TALK_ABOUT_IT, user_uttr["text"])
    if isno or not_want:
        flag = False

    logger.info(f"tell_fact_request={flag}")
    return flag


def tell_fact_response(vars):
    shared_memory = state_utils.get_shared_memory(vars)
    user_uttr = state_utils.get_last_human_utterance(vars)
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    isyes = is_yes(state_utils.get_last_human_utterance(vars))
    wikipedia_page = shared_memory.get("cur_wikipedia_page", "")
    wikihow_page = shared_memory.get("cur_wikihow_page", "")
    used_wikihow_nums_dict = shared_memory.get("used_wikihow_nums", {})
    used_wikihow_nums = used_wikihow_nums_dict.get(wikihow_page, [])
    used_wikipedia_nums_dict = shared_memory.get("used_wikipedia_nums", {})
    used_wikipedia_nums = used_wikipedia_nums_dict.get(wikipedia_page, [])
    wikipedia_page_content_list = facts_memory.get("wikipedia_content", [])
    if not wikipedia_page:
        facts_memory["wikipedia_content"] = []
    logger.info(f"wikihow_page {wikihow_page} wikipedia_page {wikipedia_page}")
    if not facts_memory.get("wikihow_content", []) and not facts_memory.get("wikipedia_content", []):
        found_entity_substr, _, found_entity_types = find_entity(vars, "current")
        state_utils.save_to_shared_memory(vars, found_entity_substr=found_entity_substr)
        state_utils.save_to_shared_memory(vars, found_entity_types=list(found_entity_types))
        logger.info(
            f"tell_fact_response, found_entity_substr {found_entity_substr} " f"found_entity_types {found_entity_types}"
        )
        wikipedia_page = get_page_title(vars, found_entity_substr)
        if wikipedia_page:
            page_content, _ = get_page_content(wikipedia_page, wikipedia_cache)
            wikipedia_page_content_list = preprocess_wikipedia_page(
                found_entity_substr, found_entity_types, page_content
            )
            facts_memory["wikipedia_content"] = wikipedia_page_content_list
            state_utils.save_to_shared_memory(vars, cur_wikipedia_page=wikipedia_page)

        wikihow_articles = []
        if found_entity_substr in wikihowq_by_substr:
            wikihow_questions = wikihowq_by_substr[found_entity_substr]
            wikihow_articles = list(wikihow_questions.keys())
        if wikihow_articles:
            wikihow_page = random.choice(wikihow_articles)
            page_content = get_wikihow_content(wikihow_page)
            wikihow_page_content_list = preprocess_wikihow_page(page_content)
            facts_memory["wikihow_content"] = wikihow_page_content_list
            state_utils.save_to_shared_memory(vars, cur_wikihow_page=wikihow_page)

    found_fact = {}
    if facts_memory.get("wikihow_content", []):
        wikihow_page_content_list = facts_memory.get("wikihow_content", [])
        logger.info(f"wikihow_content {wikihow_page_content_list[:2]}")
        for num, fact in enumerate(wikihow_page_content_list):
            if num not in used_wikihow_nums:
                found_fact = fact
                used_wikihow_nums.append(num)
                used_wikihow_nums_dict[wikihow_page] = used_wikihow_nums
                state_utils.save_to_shared_memory(vars, used_wikihow_nums=used_wikihow_nums_dict)
                break
        if len(wikihow_page_content_list) == len(used_wikihow_nums):
            state_utils.save_to_shared_memory(vars, cur_wikihow_page="")
            facts_memory["wikihow_content"] = []
    if not found_fact and facts_memory.get("wikipedia_content", []):
        wikipedia_page_content_list = facts_memory.get("wikipedia_content", [])
        logger.info(f"wikipedia_content {wikipedia_page_content_list[:2]}")
        for num, fact in enumerate(wikipedia_page_content_list):
            if num not in used_wikipedia_nums:
                found_fact = fact
                used_wikipedia_nums.append(num)
                used_wikipedia_nums_dict[wikipedia_page] = used_wikipedia_nums
                state_utils.save_to_shared_memory(vars, used_wikipedia_nums=used_wikipedia_nums_dict)
                break
        if len(wikipedia_page_content_list) == len(used_wikipedia_nums):
            state_utils.save_to_shared_memory(vars, cur_wikipedia_page="")
            facts_memory["wikipedia_content"] = []

    response = ""
    if found_fact:
        facts_str = found_fact.get("facts_str", "")
        question = found_fact.get("question", "")
        response = f"{facts_str} {question}".strip().replace("  ", " ")
    if response:
        _, conf_type = if_switch_wiki_skill(user_uttr, bot_uttr)
        must_switch = if_must_switch(user_uttr, bot_uttr)
        state_utils.set_confidence(vars, confidence=conf_type)
        if isyes or must_switch:
            state_utils.set_can_continue(vars, continue_flag=common_constants.MUST_CONTINUE)
            state_utils.set_confidence(vars, confidence=CONF_DICT["HIGH_CONF"])
        else:
            state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
            state_utils.set_confidence(vars, confidence=CONF_DICT[conf_type])
        state_utils.save_to_shared_memory(vars, start=True)
    else:
        state_utils.set_confidence(vars, confidence=CONF_DICT["UNDEFINED"])
        state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_NOT_CONTINUE)
    return response


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
    chosen_title, chosen_page_title = get_title_info(
        vars, found_entity_substr, found_entity_types, "", [], page_content
    )
    titles_q, titles_we_use, all_titles = get_titles(found_entity_substr, found_entity_types, page_content)
    question = ""
    if chosen_title:
        question = make_question(chosen_title, titles_q, found_entity_substr, [])
    chosen_title, chosen_page_title = choose_title(vars, all_titles, titles_we_use, "", [], curr_pages)
    response = question.strip()
    if chosen_title:
        used_titles.append(chosen_title)
    save_wiki_vars(
        vars,
        found_entity_substr_list,
        curr_pages,
        chosen_title,
        chosen_page_title,
        used_titles,
        found_entity_types_list,
        False,
    )
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
    nounphrases = annotations.get("spacy_nounphrases", [])
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
    save_wiki_vars(
        vars, found_entity_substr_list, curr_pages, chosen_title, chosen_page_title, used_titles, [[]], new_page
    )
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
    nounphrases = user_annotations.get("spacy_nounphrases", [])
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
        res = requests.post(
            text_qa_url, json={"question_raw": [user_uttr["text"]], "top_facts": [clean_paragraphs]}, timeout=1.0
        )
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


def error_response(vars):
    facts_memory["wikihow_content"] = []
    facts_memory["wikipedia_content"] = []

    state_utils.save_to_shared_memory(vars, cur_wikihow_page="")
    state_utils.save_to_shared_memory(vars, cur_wikipedia_page="")
    state_utils.save_to_shared_memory(vars, used_wikihow_nums={})
    state_utils.save_to_shared_memory(vars, used_wikipedia_nums={})

    state_utils.save_to_shared_memory(vars, start=False)
    save_wiki_vars(vars, [], [], "", "", [], [], False)
    state_utils.save_to_shared_memory(vars, wikihow_article="")
    state_utils.save_to_shared_memory(vars, prev_wikihow_title="")
    state_utils.save_to_shared_memory(vars, used_wikihow_titles=[])
    state_utils.save_to_shared_memory(vars, interrupted_skill="")
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_NOT_CONTINUE)
    state_utils.set_confidence(vars, 0)
    delete_topic_info(vars)
    return ""


simplified_dialog_flow = dialogflow_extension.DFEasyFilling(State.USR_START)

simplified_dialog_flow.add_user_serial_transitions(
    State.USR_START,
    {
        State.SYS_TOPIC_SMALLTALK: special_topic_request,
        State.SYS_TOPIC_FACT: special_topic_facts_request,
        State.SYS_NEWS_STEP: news_step_request,
        State.SYS_INTRO_Q: intro_question_request,
        State.SYS_TELL_FACT: tell_fact_request,
    },
)

# State.SYS_WIKIHOW_Q: wikihow_question_request,
# State.SYS_FACTOID_Q: factoid_q_request,

simplified_dialog_flow.add_user_serial_transitions(
    State.USR_TOPIC_SMALLTALK,
    {
        State.SYS_TOPIC_FACT: special_topic_facts_request,
        State.SYS_TOPIC_SMALLTALK: special_topic_request,
    },
)

simplified_dialog_flow.add_user_serial_transitions(
    State.USR_TOPIC_FACT,
    {
        State.SYS_TOPIC_SMALLTALK: special_topic_request,
        State.SYS_TOPIC_FACT: special_topic_facts_request,
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
    State.USR_TELL_FACT,
    {
        State.SYS_TELL_FACT: tell_fact_request,
    },
)

# State.SYS_FACTOID_Q: factoid_q_request,
# State.SYS_MORE_DETAILED: more_details_request,

simplified_dialog_flow.add_user_serial_transitions(
    State.USR_NEWS_STEP,
    {
        State.SYS_NEWS_STEP: news_step_request,
        State.SYS_TELL_FACT: tell_fact_request,
    },
)

simplified_dialog_flow.add_system_transition(
    State.SYS_TOPIC_SMALLTALK,
    State.USR_TOPIC_SMALLTALK,
    special_topic_response,
)
simplified_dialog_flow.add_system_transition(
    State.SYS_TOPIC_FACT,
    State.USR_TOPIC_FACT,
    special_topic_facts_response,
)
simplified_dialog_flow.add_system_transition(
    State.SYS_WIKIHOW_Q,
    State.USR_WIKIHOW_Q,
    wikihow_question_response,
)
simplified_dialog_flow.add_system_transition(
    State.SYS_WIKIHOW_STEP,
    State.USR_WIKIHOW_STEP,
    wikihow_step_response,
)
simplified_dialog_flow.add_system_transition(
    State.SYS_INTRO_Q,
    State.USR_INTRO_Q,
    intro_question_response,
)
simplified_dialog_flow.add_system_transition(
    State.SYS_TELL_FACT,
    State.USR_TELL_FACT,
    tell_fact_response,
)
simplified_dialog_flow.add_system_transition(
    State.SYS_FACTOID_Q,
    State.USR_FACTOID_Q,
    factoid_q_response,
)
simplified_dialog_flow.add_system_transition(
    State.SYS_MORE_DETAILED,
    State.USR_MORE_DETAILED,
    more_details_response,
)
simplified_dialog_flow.add_system_transition(
    State.SYS_NEWS_STEP,
    State.USR_NEWS_STEP,
    news_step_response,
)
simplified_dialog_flow.add_system_transition(
    State.SYS_ERR,
    (scopes.MAIN, scopes.State.USR_ROOT),
    error_response,
)

simplified_dialog_flow.set_error_successor(State.USR_START, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.SYS_TOPIC_SMALLTALK, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.USR_TOPIC_SMALLTALK, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.SYS_TOPIC_FACT, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.USR_TOPIC_FACT, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.SYS_TELL_FACT, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.USR_TELL_FACT, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.SYS_INTRO_Q, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.USR_INTRO_Q, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.SYS_WIKIHOW_Q, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.USR_WIKIHOW_Q, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.SYS_WIKIHOW_STEP, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.USR_WIKIHOW_STEP, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.SYS_MORE_DETAILED, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.USR_MORE_DETAILED, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.SYS_FACTOID_Q, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.USR_FACTOID_Q, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.SYS_NEWS_STEP, State.SYS_ERR)
simplified_dialog_flow.set_error_successor(State.USR_NEWS_STEP, State.SYS_ERR)

dialogflow = simplified_dialog_flow.get_dialogflow()
