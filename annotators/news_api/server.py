#!/usr/bin/env python

import logging
import os
import string
from concurrent.futures import ThreadPoolExecutor
from os import getenv
from time import time

import numpy as np
import sentry_sdk
from flask import Flask, request, jsonify
from nltk.tokenize import word_tokenize

from common.metrics import setup_metrics
from common.news import extract_topics
from newsapi_service import CachedRequestsAPI


sentry_sdk.init(getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
setup_metrics(app)

N_FACTS_TO_CHOSE = 3
ASYNC_SIZE = int(os.environ.get('ASYNC_SIZE', 5))


NEWS_API_REQUESTOR = CachedRequestsAPI(renew_freq_time=3600)  # time in seconds


def remove_punct_and_articles(s, lowecase=True):
    articles = ['a', 'the']
    if lowecase:
        s = s.lower()
    no_punct = ''.join([c for c in s if c not in string.punctuation])
    no_articles = ' '.join([w for w in word_tokenize(no_punct) if w.lower() not in articles])
    return no_articles


def collect_topics_and_statuses(dialogs):
    topics = []
    which_topics = []
    dialog_ids = []
    # list of already discussed news' urls!! so, list of strings! not list of dicts!
    prev_news_samples = []
    for i, dialog in enumerate(dialogs):
        curr_uttr = dialog["human_utterances"][-1]
        human_attr = {}
        human_attr["news_api_skill"] = dialogs[i]["human"]["attributes"].get("news_api_skill", {})
        human_attr["news_api_skill"]["discussed_news"] = human_attr["news_api_skill"].get("discussed_news", [])

        prev_bot_uttr = dialog["bot_utterances"][-1] if len(dialog["bot_utterances"]) > 0 else {"text": ""}

        topics.append("all")
        which_topics.append("all")
        dialog_ids.append(i)
        prev_news_samples.append(human_attr["news_api_skill"]["discussed_news"])

        for entity in extract_topics(curr_uttr):
            entity = remove_punct_and_articles(entity)
            topics.append(entity)
            which_topics.append("human")
            dialog_ids.append(i)
            prev_news_samples.append(human_attr["news_api_skill"]["discussed_news"])
            logger.info(f"For curr_uttr: {curr_uttr} extracted topics: {entity}.")

        for entity in extract_topics(prev_bot_uttr):
            entity = remove_punct_and_articles(entity)
            topics.append(entity)
            which_topics.append("bot")
            dialog_ids.append(i)
            prev_news_samples.append(human_attr["news_api_skill"]["discussed_news"])
            logger.info(f"For prev_bot_uttr: {prev_bot_uttr} extracted topics: {entity}.")
    return topics, which_topics, dialog_ids, prev_news_samples


@app.route("/respond", methods=['POST'])
def respond():
    st_time = time()
    dialogs = request.json['dialogs']

    try:
        topics, which_topics, dialog_ids, prev_news_samples_urls = collect_topics_and_statuses(dialogs)
        statuses = ["headline"] * len(topics)

        topics = np.array(topics)
        which_topics = np.array(which_topics)
        dialog_ids = np.array(dialog_ids)
        prev_news_samples_urls = np.array(prev_news_samples_urls)

        # run asynchronous news requests
        results = []
        executor = ThreadPoolExecutor(max_workers=ASYNC_SIZE)
        for i, result in enumerate(executor.map(NEWS_API_REQUESTOR.send, topics, statuses, prev_news_samples_urls)):
            # result is a list of articles. the first one is top rated news.
            # curr_topic = topics[i]
            # which_topic = which_topics[i]  # all, human or bot
            result = result if (result and result.get("title") and result.get("description")) else {}
            logger.info(f"Result: {result}.")
            results.append(result)

        results = np.array(results)
        topics = np.array(topics)
        which_topics = np.array(which_topics)
        dialog_ids = np.array(dialog_ids)

        responses = []
        for i, dialog in enumerate(dialogs):
            curr_results = results[dialog_ids == i]
            curr_topics = topics[dialog_ids == i]
            curr_which_topics = which_topics[dialog_ids == i]

            curr_response = []
            for topic, which_topic, result in zip(curr_topics, curr_which_topics, curr_results):
                curr_response.append({"entity": topic, "which": which_topic, "news": result})
            responses.append(curr_response)

    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
        responses = []
        for _ in dialogs:
            responses.append([{}])

    total_time = time() - st_time
    logger.info(f'news_api_skill exec time: {total_time:.3f}s')
    return jsonify(responses)


@app.route("/healthz", methods=['GET'])
def healthz():
    return "OK", 200


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
