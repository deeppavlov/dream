import logging
import os
import requests
from os import getenv
from datetime import datetime
import sentry_sdk
from langdetect import detect
from collections import deque


sentry_sdk.init(getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


BLACKLIST_ANNOTATOR_URL = getenv('BLACKLIST_ANNOTATOR_URL')


class CachedRequestsAPI:
    NEWS_SERVICE_URL = f"http://newsapi.org/v2/top-headlines?q=TOPIC&sortBy=popularity&apiKey="
    ALL_NEWS_SERVICE_URL = f"http://newsapi.org/v2/top-headlines?sources=bbc-news&apiKey="

    def __init__(self, renew_freq_time=3600):
        self.renew_freq_time = renew_freq_time
        self.first_renew_time = datetime.now()
        self.prev_renew_times = {}
        self.cached = {}
        self._api_keys = self._collect_api_keys()
        logger.info(f"CachedRequestAPI initialized with renew_freq_time: {renew_freq_time} s;"
                    f"api keys: {self._api_keys}")

    def _collect_api_keys(self):
        api_keys_count = 5
        api_keys = []
        for i in range(1, api_keys_count + 1):
            key = f"NEWS_API_KEY_{i}"
            if key in os.environ:
                api_keys.append(os.environ[key])
        assert len(api_keys) > 0, print(f"news skill api keys is empty! api_keys {api_keys}")
        return deque(api_keys)

    def _construct_address(self, topic, api_key):
        if topic == "all":
            request_address = self.ALL_NEWS_SERVICE_URL + api_key
        else:
            request_address = self.NEWS_SERVICE_URL + api_key
            request_address = request_address.replace("TOPIC", topic)
        return request_address

    def _make_request(self, topic):
        for ind, api_key in enumerate(self._api_keys):
            try:
                request_address = self._construct_address(topic, api_key)
                resp = requests.get(url=request_address, timeout=0.7)
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
        return resp

    def get_new_topic_news(self, topic):
        result = []
        resp = self._make_request(topic)

        if resp.status_code != 200:
            logger.warning(
                f"result status code is not 200: {resp}. result text: {resp.text}; "
                f"result status: {resp.status_code}")
            sentry_sdk.capture_message(
                f"News API! result status code is not 200: {resp}. result text: {resp.text}; "
                f"result status: {resp.status_code}")
        else:
            response = resp.json()
            if response["status"] != "ok":
                logger.warning(
                    f"News API! result status code is not `ok`")
                sentry_sdk.capture_message(
                    f"News API! result status code is not `ok`")
            else:
                response = response.get("articles", [])
                result = response
        return result

    def send(self, topic="all", status="", prev_news={}):
        """Get news using cache and NewsAPI requests

        Args:
            topic: string topic (i.g. sport news, putin, politics
            status: string news skill status
            prev_news: prev news sent to user (dictionary)

        Returns:
            dictionary with one top rated over latest news
        """
        topic = topic.lower() if len(topic) > 0 else "all"
        curr_time = datetime.now()

        if len(self.cached.get(topic, [])) == 0 or \
                (curr_time - self.prev_renew_times.get(topic, self.first_renew_time)).seconds > self.renew_freq_time:
            self.cached[topic] = self.get_new_topic_news(topic) + self.cached.get(topic, [])
            self.prev_renew_times[topic] = curr_time

        top_news = self.cached.get(topic, [])

        if len(top_news) > 0:
            if prev_news != {} and status == "headline":
                # some prev discussed news detected
                try:
                    prev_index = self.cached[topic].index(prev_news)
                except ValueError:
                    # prev news is not stored anymore or from other topic
                    prev_index = -1
                if prev_index == len(self.cached[topic]) - 1:
                    # out of available news
                    result = {}
                else:
                    # return the next one news in top rating
                    result = self.get_not_blacklisted_english_news(self.cached[topic][prev_index + 1:])
            else:
                result = self.get_not_blacklisted_english_news(top_news)
        else:
            result = {}
        return result

    @staticmethod
    def get_not_blacklisted_english_news(articles):
        for article in articles:
            title = article.get("title", "") or ""
            if len(title) == 0:
                continue
            description = article.get("description", "") or ""
            if len(description) == 0:
                continue
            lang = detect(article.get("title", ""))
            if lang != "en":
                continue

            to_check = [f"{title} {description}"]

            try:
                resp = requests.request(url=BLACKLIST_ANNOTATOR_URL, json={"sentences": to_check},
                                        method="POST", timeout=1.5)
            except (requests.ConnectTimeout, requests.ReadTimeout) as e:
                sentry_sdk.capture_exception(e)
                logger.exception("Blacklisted Annotator requests from News API skill Timeout")
                resp = requests.Response()
                resp.status_code = 504

            if resp.status_code != 200:
                logger.warning(
                    f"result status code is not 200: {resp}. result text: {resp.text}; "
                    f"result status: {resp.status_code}")
                result = False
                sentry_sdk.capture_message(
                    f"Blacklisted Annotator requests from News API skill "
                    f" result status code is not 200: {resp}. result text: {resp.text}; "
                    f"result status: {resp.status_code}")
            else:
                # each element is like `{'inappropriate': False, 'profanity': False, 'restricted_topics': False}`
                result = [d.get("inappropriate", False) or d.get("profanity", False)
                          for d in resp.json()[0]["batch"]][0]

            if not result:
                return article
            else:
                continue

        return {}
