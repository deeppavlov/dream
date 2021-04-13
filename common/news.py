import logging
import random
import re
import requests
from os import getenv

import sentry_sdk

from common.utils import is_yes

sentry_sdk.init(getenv('SENTRY_DSN'))

logger = logging.getLogger(__name__)

# this way news skill offers latest news when nothing specific found
OFFER_BREAKING_NEWS = "Would you like to hear the latest news?"
OFFER_TOPIC_SPECIFIC_NEWS = "Would you like to hear news about TOPIC?"
# statuses in attributes for news skill
OFFER_TOPIC_SPECIFIC_NEWS_STATUS = "offered_specific_news"
OFFERED_BREAKING_NEWS_STATUS = "offered_breaking_news"
OFFERED_NEWS_DETAILS_STATUS = "offered_news_details"
OPINION_REQUEST_STATUS = "opinion_request"
OFFERED_NEWS_TOPIC_CATEGORIES_STATUS = "offered_news_topic_categories"

NEWS_GIVEN = "offered_news_details"
WHAT_TYPE_OF_NEWS = ["What other kinds of news would you want to discuss?",
                     "What are the other kinds of news would you like to hear about?",
                     "What else would you want to hear news about?",
                     "What type of news do you prefer?"]

NEWS_DUPLICATES = WHAT_TYPE_OF_NEWS
NEWS_COMPILED_PATTERN = re.compile(r"(news|(what is|what ?'s)( the)? new|something new)", re.IGNORECASE)


def skill_trigger_phrases():
    return [OFFER_BREAKING_NEWS]


def is_breaking_news_requested(prev_bot_utt, user_utt):
    if OFFER_BREAKING_NEWS.lower() in prev_bot_utt.get('text', '').lower():
        if is_yes(user_utt):
            return True
    return False


TOPIC_NEWS_OFFER = [
    "Would you like to hear something new about",
    "Would you like to hear news about"
]


def get_offer_news_about_topic(topic):
    return f"{random.choice(TOPIC_NEWS_OFFER)} {topic}?"


def was_offer_news_about_topic(uttr: str):
    uttr_lower = uttr.lower()
    if any([offer.lower() in uttr_lower for offer in TOPIC_NEWS_OFFER]):
        return True
    return False


def get_news_about_topic(topic: str, NEWS_API_SKILL_URL: str):
    """
    Function to get news output from news-api-skill.
    ```
    import os

    NEWS_API_SKILL_URL = os.environ.get('NEWS_API_SKILL_URL')
    result = get_news_about_topic("politics", NEWS_API_SKILL_URL)
    result = [text, conf, human_attributes, bot_attributes, attributes]
    ```
        attributes contains `curr_news` dictionary with info about news
    """
    # 'curr_news': {
    # 'content': "MORLEY -- Braelyn Berry will be doing her third sport with the track team in her junior season.\n
    #     But she's had some outstanding efforts in her other two sports.\nBerry was an All-Stater with the volleyball
    #     team in the fall and a standout with her baske... [1299 chars]",
    # 'description': 'MORLEY -- Braelyn Berry will be doing her third sport with the track team in her junior...',
    # 'image': 'https://s.hdnux.com/photos/01/17/44/57/20859886/3/rawImage.jpg',
    # 'publishedAt': '2021-04-13T02:43:00Z',
    # 'source': {'name': 'The Pioneer', 'url': 'https://www.bigrapidsnews.com'},
    # 'title': 'Morley Stanwood multi-sport athlete anxious for spring season',
    # 'url': 'https://www.bigrapidsnews.com/sports/article/Morley-Stanwood-multi-sport-athlete-anxious-for-16096053.php'
    # },
    dialogs = {"dialogs": [
        {"utterances": [],
         "bot_utterances": [],
         "human": {"attributes": {}},
         "human_utterances": [
            {
                "text": f"news about {topic}",
                "annotations":
                    {
                        "ner": [[{"text": topic}]],
                        "cobot_topics": {
                            "text": [
                                "News"
                            ]
                        }
                    }
            }
        ]
        }
    ]}
    try:
        result = requests.post(NEWS_API_SKILL_URL, json=dialogs, timeout=1.5)
        result = result.json()[0]
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
        result = []

    return result
