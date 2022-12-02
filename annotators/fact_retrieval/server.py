import json
import logging
import nltk
import os
import pickle
import re
import time

import numpy as np
import sentry_sdk
from flask import Flask, request, jsonify
from sentry_sdk.integrations.flask import FlaskIntegration
from deeppavlov import build_model

from common.fact_retrieval import topic_titles, find_topic_titles
from common.wiki_skill import find_all_titles, find_paragraph, delete_hyperlinks, WIKI_BADLIST

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

FILTER_FREQ = False

CONFIG = os.getenv("CONFIG")
CONFIG_PAGE_EXTRACTOR = os.getenv("CONFIG_WIKI")
CONFIG_WOW_PAGE_EXTRACTOR = os.getenv("CONFIG_WHOW")
N_FACTS = int(os.getenv("N_FACTS", 3))

DATA_GOOGLE_10K_ENG_NO_SWEARS = "common/google-10000-english-no-swears.txt"
DATA_SENTENCES = "data/sentences.pickle"

re_tokenizer = re.compile(r"[\w']+|[^\w ]")

with open(DATA_GOOGLE_10K_ENG_NO_SWEARS, "r") as fl:
    lines = fl.readlines()
    freq_words = [line.strip() for line in lines]
    freq_words = set(freq_words[:800])

with open("%s" % DATA_SENTENCES, "rb") as fl:
    test_sentences = pickle.load(fl)

try:
    fact_retrieval = build_model(CONFIG, download=True)

    with open("/root/.deeppavlov/downloads/wikidata/entity_types_sets.pickle", "rb") as fl:
        entity_types_sets = pickle.load(fl)

    page_extractor = build_model(CONFIG_PAGE_EXTRACTOR, download=True)
    logger.info("model loaded, test query processed")

    whow_page_extractor = build_model(CONFIG_WOW_PAGE_EXTRACTOR, download=True)

    with open("/root/.deeppavlov/downloads/wikihow/wikihow_topics.json", "r") as fl:
        wikihow_topics = json.load(fl)
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = Flask(__name__)


def get_page_content(page_title):
    page_content = {}
    try:
        if page_title:
            page_content_batch, main_pages_batch = page_extractor([[page_title]])
            if page_content_batch and page_content_batch[0]:
                page_content = page_content_batch[0][0]
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)

    return page_content


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


def find_sentences(paragraphs):
    sentences_list = []
    if paragraphs:
        paragraph = paragraphs[0]
        paragraph, mentions, mention_pages = delete_hyperlinks(paragraph)
        sentences = nltk.sent_tokenize(paragraph)
        cur_len = 0
        max_len = 50
        for sentence in sentences:
            words = re.findall(re_tokenizer, sentence)
            if cur_len + len(words) < max_len and not re.findall(WIKI_BADLIST, sentence):
                sentences_list.append(sentence)
                cur_len += len(words)
    return sentences_list


def find_facts(entity_substr_batch, entity_ids_batch, entity_pages_batch):
    facts_batch = []
    for entity_substr_list, entity_ids_list, entity_pages_list in zip(
        entity_substr_batch, entity_ids_batch, entity_pages_batch
    ):
        facts_list = []
        for entity_substr, entity_ids, entity_pages in zip(entity_substr_list, entity_ids_list, entity_pages_list):
            for entity_id, entity_page in zip(entity_ids, entity_pages):
                for entity_types_substr in entity_types_sets:
                    if entity_id in entity_types_sets[entity_types_substr]:
                        logger.info(f"found_entity_types_substr {entity_types_substr} entity_page {entity_page}")
                        if entity_types_substr in {"food", "fruit", "vegetable", "berry"}:
                            found_page_title = ""
                            entity_tokens = set(re.findall(re_tokenizer, entity_substr))
                            food_subtopics = wikihow_topics["Food and Entertaining"]
                            for subtopic in food_subtopics:
                                page_titles = food_subtopics[subtopic]
                                for page_title in page_titles:
                                    page_title_tokens = set(page_title.lower().split("-"))
                                    if entity_tokens.intersection(page_title_tokens):
                                        found_page_title = page_title
                                        break
                                if found_page_title:
                                    break
                            if found_page_title:
                                page_content = get_wikihow_content(found_page_title)
                                if page_content:
                                    page_title_clean = found_page_title.lower().replace("-", " ")
                                    intro = page_content["intro"]
                                    sentences = nltk.sent_tokenize(intro)
                                    facts_list.append(
                                        {
                                            "entity_substr": entity_substr,
                                            "entity_type": entity_types_substr,
                                            "facts": [{"title": page_title_clean, "sentences": sentences}],
                                        }
                                    )
                        else:
                            facts = []
                            page_content = get_page_content(entity_page)
                            all_titles = find_all_titles([], page_content)
                            if entity_types_substr in topic_titles:
                                cur_topic_titles = topic_titles[entity_types_substr]
                                page_titles = find_topic_titles(all_titles, cur_topic_titles)
                                for title, page_title in page_titles:
                                    paragraphs = find_paragraph(page_content, page_title)
                                    sentences_list = find_sentences(paragraphs)
                                    if sentences_list:
                                        facts.append({"title": title, "sentences": sentences_list})
                                if facts:
                                    facts_list.append(
                                        {
                                            "entity_substr": entity_substr,
                                            "entity_type": entity_types_substr,
                                            "facts": list(np.random.choice(facts, size=N_FACTS, replace=False)),
                                        }
                                    )
        facts_batch.append(
            list(np.random.choice(facts_list, size=N_FACTS, replace=False)) if len(facts_list) > 0 else facts_list
        )
    return facts_batch


@app.route("/model", methods=["POST"])
def respond():
    st_time = time.time()
    cur_utt = request.json.get("human_sentences", [" "])
    dialog_history = request.json.get("dialog_history", [" "])
    cur_utt = [utt.lstrip("alexa") for utt in cur_utt]
    nounphr_list = request.json.get("nounphrases", [])
    if FILTER_FREQ:
        nounphr_list = [
            [nounphrase for nounphrase in nounphrases if nounphrase not in freq_words] for nounphrases in nounphr_list
        ]
    if not nounphr_list:
        nounphr_list = [[] for _ in cur_utt]

    entity_substr = request.json.get("entity_substr", [])
    if not entity_substr:
        entity_substr = [[] for _ in cur_utt]
    entity_pages = request.json.get("entity_pages", [])
    if not entity_pages:
        entity_pages = [[] for _ in cur_utt]
    entity_pages_titles = request.json.get("entity_pages_titles", [])
    if not entity_pages_titles:
        entity_pages_titles = [[] for _ in cur_utt]
    entity_ids = request.json.get("entity_ids", [])
    if not entity_ids:
        entity_ids = [[] for _ in cur_utt]
    logger.info(
        f"cur_utt {cur_utt} dialog_history {dialog_history} nounphr_list {nounphr_list} entity_pages {entity_pages}"
    )

    nf_numbers, f_utt, f_dh, f_nounphr_list, f_entity_pages = [], [], [], [], []
    for n, (utt, dh, nounphrases, input_pages) in enumerate(zip(cur_utt, dialog_history, nounphr_list, entity_pages)):
        if utt not in freq_words and nounphrases:
            f_utt.append(utt)
            f_dh.append(dh)
            f_nounphr_list.append(nounphrases)
            f_entity_pages.append(input_pages)
        else:
            nf_numbers.append(n)

    out_res = [{"facts": [], "topic_facts": []} for _ in cur_utt]
    try:
        facts_batch = find_facts(entity_substr, entity_ids, entity_pages_titles)
        logger.info(f"f_utt {f_utt}")
        if f_utt:
            fact_res = fact_retrieval(f_utt) if len(f_utt[0].split()) > 3 else fact_retrieval(f_dh)
            if fact_res:
                fact_res = fact_res[0]
            fact_res = [[fact.replace('""', '"') for fact in facts] for facts in fact_res]

            out_res = []
            cnt_fnd = 0
            for i in range(len(cur_utt)):
                if i in nf_numbers:
                    out_res.append({})
                else:
                    if cnt_fnd < len(fact_res):
                        out_res.append(
                            {
                                "topic_facts": facts_batch[cnt_fnd],
                                "facts": list(np.random.choice(fact_res[cnt_fnd], size=N_FACTS, replace=False))
                                if len(fact_res[cnt_fnd]) > 0
                                else fact_res[cnt_fnd],
                            }
                        )
                        cnt_fnd += 1
                    else:
                        out_res.append({"facts": [], "topic_facts": []})
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
    total_time = time.time() - st_time
    logger.info(f"fact_retrieval exec time: {total_time:.3f}s")
    return jsonify(out_res)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
