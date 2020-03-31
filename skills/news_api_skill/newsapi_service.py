import logging
import os
import requests
from os import getenv
from datetime import datetime
import sentry_sdk
from langdetect import detect
from copy import deepcopy


sentry_sdk.init(getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

NEWS_API_KEY = os.environ.get('NEWS_API_KEY')
NEWS_SERVICE_URL = f"http://newsapi.org/v2/top-headlines?q=TOPIC&sortBy=popularity&apiKey={NEWS_API_KEY}"
ALL_NEWS_SERVICE_URL = f"http://newsapi.org/v2/top-headlines?sources=bbc-news&apiKey={NEWS_API_KEY}"

if NEWS_API_KEY is None:
    raise RuntimeError('NEWS_API_KEY environment variable is not set')


class CachedRequestsAPI:
    def __init__(self, renew_freq_time=3600):
        self.renew_freq_time = renew_freq_time
        self.prev_renew_time = datetime.now()
        self.cached = {}
        logger.info(f"CachedRequestAPI initialized with renew_freq_time: {renew_freq_time} s")

    def send(self, topic="all"):
        """Get news using cache and NewsAPI requests

        Args:
            topic: string topic (i.g. sport news, putin, politics

        Returns:
            dictionary with one top rated over latest news
        """
        topic = topic.lower()

        curr_time = datetime.now()
        if (curr_time - self.prev_renew_time).seconds > self.renew_freq_time:
            self.cached = {}
            self.prev_renew_time = curr_time

        if len(topic) == 0:
            topic = "all"
        # use cache
        if len(self.cached.get(topic, [])) > 0:
            return self.cached[topic]

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
                self.cached[topic] = self.get_only_english_news(response) + self.cached.get(topic, [])

        if len(self.cached.get(topic, [])) == 0:
            return [{}]
        else:
            return self.cached[topic]

    def get_only_english_news(self, articles):
        en_articles = []

        for article in articles:
            lang = detect(article.get("title", "title"))
            if lang == "en":
                en_articles.append(deepcopy(article))

        if len(en_articles) == 0 and len(articles) > 0:
            # didn't find english news, take just the top rated one
            en_articles.append(deepcopy(articles[0]))
        return en_articles
