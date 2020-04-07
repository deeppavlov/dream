import logging
import os
import requests
from os import getenv
from datetime import datetime
import sentry_sdk
from langdetect import detect


sentry_sdk.init(getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

NEWS_API_KEY = os.environ.get('NEWS_API_KEY')
NEWS_SERVICE_URL = f"http://newsapi.org/v2/top-headlines?q=TOPIC&sortBy=popularity&apiKey={NEWS_API_KEY}"
ALL_NEWS_SERVICE_URL = f"http://newsapi.org/v2/top-headlines?sources=bbc-news&apiKey={NEWS_API_KEY}"

if NEWS_API_KEY is None:
    raise RuntimeError('NEWS_API_KEY environment variable is not set')

BLACKLIST_ANNOTATOR_URL = "http://blacklisted_words:8018/blacklisted_words_batch"


class CachedRequestsAPI:
    def __init__(self, renew_freq_time=3600):
        self.renew_freq_time = renew_freq_time
        self.prev_renew_time = datetime.now()
        self.cached = {}
        logger.info(f"CachedRequestAPI initialized with renew_freq_time: {renew_freq_time} s")

    def send(self, topic="all", status="", prev_news={}):
        """Get news using cache and NewsAPI requests

        Args:
            topic: string topic (i.g. sport news, putin, politics
            status: string news skill status
            prev_news: prev news sent to user (dictionary)

        Returns:
            dictionary with one top rated over latest news
        """
        topic = topic.lower()
        top_news = []

        curr_time = datetime.now()
        if (curr_time - self.prev_renew_time).seconds > self.renew_freq_time:
            self.cached = {}
            self.prev_renew_time = curr_time

        if len(topic) == 0:
            topic = "all"
        # use cache
        if len(self.cached.get(topic, [])) > 0:
            top_news = self.cached[topic]

        try:
            if topic == "all":
                request_address = ALL_NEWS_SERVICE_URL
            else:
                request_address = NEWS_SERVICE_URL.replace("TOPIC", topic)
            resp = requests.get(url=request_address)
        except (requests.ConnectTimeout, requests.ReadTimeout) as e:
            sentry_sdk.capture_exception(e)
            logger.exception("NewsAPI Timeout")
            resp = requests.Response()
            resp.status_code = 504

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
                self.cached[topic] = response + self.cached.get(topic, [])

        if len(self.cached.get(topic, [])) == 0:
            self.cached[topic] = []
            top_news = [{}]
        else:
            top_news = self.cached[topic]

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
            title = article.get("title", "title")
            description = article.get("description", "description")
            lang = detect(article.get("title", "title"))
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
