import json
import logging
import os
import random
import re
import nltk
import requests
import sentry_sdk
import common.constants as common_constants
import common.dff.integration.context as context

from common.wiki_skill import (
    find_page_title,
    find_all_titles,
    find_paragraph,
    used_types_dict,
    delete_hyperlinks,
    NEWS_MORE,
    QUESTION_TEMPLATES,
    QUESTION_TEMPLATES_SHORT,
    WIKI_BADLIST,
)
from common.utils import is_no, is_yes
from common.universal_templates import CONTINUE_PATTERN

nltk.download("punkt")

sentry_sdk.init(os.getenv("SENTRY_DSN"))
logger = logging.getLogger(__name__)
WIKI_FACTS_URL = os.getenv("WIKI_FACTS_URL")

with open("/src/common/wikihow_cache.json", "r") as fl:
    wikihow_cache = json.load(fl)

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


def get_wikipedia_content(page_title, cache_page_dict=None):
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


def get_wikihow_content(page_title, cache_page_dict=None):
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


def provide_facts_request(ctx, actor):
    flag = False
    wiki = ctx.misc.get("wiki", {})
    user_uttr: dict = ctx.misc.get("agent", {}).get("dialog", {}).get("human_utterances", [{}])[-1]
    isno = is_no(user_uttr)
    cur_wiki_page = wiki.get("cur_wiki_page", "")
    if cur_wiki_page:
        wiki_page_content_list = memory.get("wiki_page_content", [])
        used_wiki_page_nums = wiki.get("used_wiki_page_nums", {}).get(cur_wiki_page, [])
        logger.info(f"request, used_wiki_page_nums {used_wiki_page_nums}")
        logger.info(f"request, wiki_page_content_list {wiki_page_content_list[:3]}")
        if len(wiki_page_content_list) > 0 and len(used_wiki_page_nums) < len(wiki_page_content_list) and not isno:
            flag = True
    return flag


def provide_facts_response(ctx, actor, page_source, wiki_page):
    wiki = ctx.misc.get("wiki", {})
    user_uttr: dict = ctx.misc.get("agent", {}).get("dialog", {}).get("human_utterances", [{}])[-1]
    isyes = is_yes(user_uttr) or re.findall(CONTINUE_PATTERN, user_uttr["text"])
    response = ""
    cur_wiki_page = wiki.get("cur_wiki_page", "")
    if not cur_wiki_page:
        wiki["cur_wiki_page"] = wiki_page
        if page_source == "wikiHow":
            page_content = get_wikihow_content(wiki_page, wikihow_cache)
            wiki_page_content_list = preprocess_wikihow_page(page_content)
            memory["wiki_page_content"] = wiki_page_content_list
        elif page_source == "wikipedia":
            page_content = get_wikipedia_content(wiki_page)
            wiki_page_content_list = preprocess_wikipedia_page(wiki_page.lower(), [], page_content)
            memory["wiki_page_content"] = wiki_page_content_list
        logger.info(f"wiki_page {wiki_page}")

    used_wiki_page_nums_dict = wiki.get("used_wiki_page_nums", {})
    used_wiki_page_nums = used_wiki_page_nums_dict.get(wiki_page, [])
    wiki_page_content_list = memory.get("wiki_page_content", [])
    logger.info(f"response, used_wiki_page_nums {used_wiki_page_nums}")
    logger.info(f"response, wiki_page_content_list {wiki_page_content_list[:3]}")

    if wiki_page_content_list:
        for num, fact in enumerate(wiki_page_content_list):
            if num not in used_wiki_page_nums:
                facts_str = fact.get("facts_str", "")
                question = fact.get("question", "")
                response = f"{facts_str} {question}".strip().replace("  ", " ")
                used_wiki_page_nums.append(num)
                used_wiki_page_nums_dict[wiki_page] = used_wiki_page_nums
                wiki["used_wiki_page_nums"] = used_wiki_page_nums_dict
                break

        if len(wiki_page_content_list) == len(used_wiki_page_nums):
            if len(wiki_page_content_list) == len(used_wiki_page_nums):
                wiki["wiki_page"] = ""
                memory["wiki_page_content"] = []
    logger.info(f"response, final {response}")
    if response:
        if isyes:
            context.set_confidence(ctx, actor, 1.0)
            context.set_can_continue(ctx, actor, common_constants.MUST_CONTINUE)
        else:
            context.set_confidence(ctx, actor, 0.99)
            context.set_can_continue(ctx, actor, common_constants.CAN_CONTINUE_SCENARIO)
    else:
        context.set_confidence(ctx, actor, 0.0)
        context.set_can_continue(ctx, actor, common_constants.CAN_NOT_CONTINUE)
    if hasattr(ctx, "a_s"):
        processed_node = ctx.a_s.get("processed_node", ctx.a_s["next_node"])
        processed_node.response = response
        ctx.a_s["processed_node"] = processed_node
    else:
        processed_node = ctx.framework_states["actor"].get("processed_node", ctx.framework_states["actor"]["next_node"])
        processed_node.response = response
        ctx.framework_states["actor"]["processed_node"] = processed_node
    return ctx
