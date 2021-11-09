import logging
import os
import requests
import re
from collections import deque
from copy import deepcopy
from datetime import datetime
from os import getenv

import sentry_sdk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.tokenize import sent_tokenize

sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


BLACKLIST_ANNOTATOR_URL = getenv("BLACKLIST_ANNOTATOR_URL")

BLACKLISTED_WORDS = re.compile(
    r"\b(gun|shoot|die.?\b|murder|kill|victim|stolen" r"|decease|sick\b|sicken\b|sickness\b|hurt\b|hurting\b|ailing\b)",
    re.IGNORECASE,
)
nltk_sentiment_classifier = SentimentIntensityAnalyzer()


def get_nltk_sentiment(text):
    result = nltk_sentiment_classifier.polarity_scores(text)
    if result.get("neg", 0.0) >= 0.05:
        return "negative"
    elif result.get("pos", 0.0) >= 0.5:
        return "positive"
    else:
        return "neutral"


class CachedRequestsAPI:
    NEWS_SERVICE_URL = f"https://gnews.io/api/v4/search?q=TOPIC&country=us&lang=en&max=20&sortby=publishedAt&token="
    ALL_NEWS_SERVICE_URL = f"https://gnews.io/api/v4/top-headlines?country=us&lang=en&max=20&sortby=publishedAt&token="
    EXT_NEWS_SERVICE_URL = (
        f"https://gnews.io/api/v4/search?q=TOPIC&country=us&lang=en&expand=content&max=5" f"&sortby=publishedAt&token="
    )
    EXT_ALL_NEWS_SERVICE_URL = (
        f"https://gnews.io/api/v4/top-headlines?country=us&lang=en&expand=content&max=5" f"&sortby=publishedAt&token="
    )

    def __init__(self, renew_freq_time=3600):
        self.renew_freq_time = renew_freq_time
        self.first_renew_time = datetime.now()
        self.prev_renew_times = {}
        self.cached = {}
        self._api_keys = self._collect_api_keys()
        logger.info(
            f"CachedRequestAPI initialized with renew_freq_time: {renew_freq_time} s;" f"api keys: {self._api_keys}"
        )

    def _collect_api_keys(self):
        api_keys = [os.environ["GNEWS_API_KEY"]]
        assert len(api_keys) > 0, print(f"news skill api keys is empty! api_keys {api_keys}")
        return deque(api_keys)

    def _construct_address(self, topic, api_key, return_list_of_news):
        if topic == "all":
            if return_list_of_news:
                request_address = self.EXT_ALL_NEWS_SERVICE_URL + api_key
            else:
                request_address = self.ALL_NEWS_SERVICE_URL + api_key
        else:
            if return_list_of_news:
                request_address = self.EXT_NEWS_SERVICE_URL + api_key
            else:
                request_address = self.NEWS_SERVICE_URL + api_key
            request_address = request_address.replace("TOPIC", f'"{topic}"')
        return request_address

    def _make_request(self, topic, return_list_of_news):
        import time
        for ind, api_key in enumerate(self._api_keys):
            try:
                t = time.time()
                request_address = self._construct_address(topic, api_key, return_list_of_news)
                resp = requests.get(url=request_address, timeout=7)
                logger.warning(time.time() - t)
                logger.warning(request_address)
            except Exception as e:
                sentry_sdk.capture_exception(e)
                logger.exception(e)
                resp = requests.Response()
                resp.status_code = 504
            if resp.status_code == 429:
                msg = f"News API Response status code 429 with api key {api_key}"
                logger.warning(msg)
            else:
                # Change order of api_keys to use first success next time
                self._api_keys.rotate(-ind)
                break
        logger.warning(resp)
        return resp

    def get_new_topic_news(self, topic, return_list_of_news):
        result = []
        resp = self._make_request(topic, return_list_of_news)

        if resp.status_code != 200:
            logger.warning(
                f"result status code is not 200: {resp}. result text: {resp.text}; "
                f"result status: {resp.status_code}"
            )
            sentry_sdk.capture_message(
                f"News API! result status code is not 200: {resp}. result text: {resp.text}; "
                f"result status: {resp.status_code}"
            )
        else:
            response = resp.json()
            response = response.get("articles", [])
            result = response
        result = self.get_not_blacklisted_english_news(result)
        return result

    def send(self, topic="all", status="", prev_news_urls=None, return_list_of_news=False):
        """Get news using cache and NewsAPI requests

        Args:
            topic: string topic (i.g. sport news, putin, politics
            status: string news skill status
            prev_news_urls: list of all discussed previous news' URLs sent to user (list of strings)
        Returns:
            dictionary with one top rated over latest news
        """
        prev_news_urls = [] if prev_news_urls is None else prev_news_urls
        topic = topic.lower() if len(topic) > 0 else "all"
        curr_time = datetime.now()

        if return_list_of_news:
            top_news = self.get_new_topic_news(topic, return_list_of_news)
        else:
            if (
                len(self.cached.get(topic, [])) == 0
                or (curr_time - self.prev_renew_times.get(topic, self.first_renew_time)).seconds > self.renew_freq_time
            ):
                self.cached[topic] = self.get_new_topic_news(topic, return_list_of_news) + self.cached.get(topic, [])
                self.prev_renew_times[topic] = curr_time

            top_news = deepcopy(self.cached.get(topic, []))

        if len(prev_news_urls) > 0 and status == "headline":
            # some prev discussed news detected
            top_news = [news for news in top_news if "url" in news and news["url"] not in prev_news_urls]

        if len(top_news) > 0:
            return top_news
        else:
            return []

    @staticmethod
    def get_not_blacklisted_english_news(articles):
        articles_to_check = []
        for article in articles:
            title = article.get("title", "") or ""
            if len(title) == 0:
                continue
            description = article.get("content", "") or ""
            sentences_content = sent_tokenize(description)
            if description and len(sentences_content) > 2:
                description = " ".join(sentences_content[:2])
                article["description"] = description
            elif description and len(sentences_content) > 1:
                description = sentences_content[0]
                article["description"] = description
            else:
                description = article.get("description", "") or ""

            if len(description) == 0:
                continue
            if get_nltk_sentiment(f"{title} {description}") == "negative":
                continue

            articles_to_check += [f"{title} {description}"]

        try:
            resp = requests.request(
                url=BLACKLIST_ANNOTATOR_URL, json={"sentences": articles_to_check}, method="POST", timeout=0.5
            )
        except (requests.ConnectTimeout, requests.ReadTimeout) as e:
            sentry_sdk.capture_exception(e)
            logger.exception("Blacklisted Annotator requests from News API Annotator Timeout")
            resp = requests.Response()
            resp.status_code = 504

        if resp.status_code != 200:
            logger.warning(
                f"result status code is not 200: {resp}. result text: {resp.text}; "
                f"result status: {resp.status_code}"
            )
            result = [False] * len(articles_to_check)
            sentry_sdk.capture_message(
                f"Blacklisted Annotator requests from News API Annotator "
                f" result status code is not 200: {resp}. result text: {resp.text}; "
                f"result status: {resp.status_code}"
            )
        else:
            # each element is like `{'inappropriate': False, 'profanity': False, 'restricted_topics': False}`
            result = [sum(d.values()) for d in resp.json()[0]["batch"]]

        articles = [
            article
            for article, is_black in zip(articles, result)
            if not is_black
            and not BLACKLISTED_WORDS.search(f'{article.get("title", "")} {article.get("description", "")}')
        ]

        return articles
