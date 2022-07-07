import logging
import random
import re
import requests
from os import getenv

import sentry_sdk
from common.utils import is_yes, get_entities

sentry_sdk.init(getenv("SENTRY_DSN"))

logger = logging.getLogger(__name__)

# this way news skill offers latest news when nothing specific found
OFFER_BREAKING_NEWS = "Would you like to hear the latest news?"
OFFER_TOPIC_SPECIFIC_NEWS = "Would you like to hear news about TOPIC?"
SAY_TOPIC_SPECIFIC_NEWS = "Talking about TOPIC. I've recently heard that"
# statuses in attributes for news skill
OFFER_TOPIC_SPECIFIC_NEWS_STATUS = "offered_specific_news"
OFFERED_BREAKING_NEWS_STATUS = "offered_breaking_news"
OFFERED_NEWS_DETAILS_STATUS = "offered_news_details"
OPINION_REQUEST_STATUS = "opinion_request"
OFFERED_NEWS_TOPIC_CATEGORIES_STATUS = "offered_news_topic_categories"

NEWS_GIVEN = "offered_news_details"
WHAT_TYPE_OF_NEWS = [
    "What other kinds of news would you want to discuss?",
    "What are the other kinds of news would you like to hear about?",
    "What else would you want to hear news about?",
    "What type of news do you prefer?",
]

NEWS_DUPLICATES = WHAT_TYPE_OF_NEWS
NEWS_COMPILED_PATTERN = re.compile(r"(news|(what is|what ?'s)( the)? new|something new)", re.IGNORECASE)
EXTRACT_OFFERED_NEWS_TOPIC_TEMPLATE = re.compile(r"news? about ([a-z\- ]+)", re.IGNORECASE)


def skill_trigger_phrases():
    return [OFFER_BREAKING_NEWS]


def is_breaking_news_requested(prev_bot_utt, user_utt):
    if OFFER_BREAKING_NEWS.lower() in prev_bot_utt.get("text", "").lower():
        if is_yes(user_utt):
            return True
    return False


TOPIC_NEWS_OFFER = ["Would you like to hear something new about", "Would you like to hear news about"]


def get_offer_news_about_topic(topic):
    return f"{random.choice(TOPIC_NEWS_OFFER)} {topic}?"


def was_offer_news_about_topic(uttr: str):
    uttr_lower = uttr.lower()
    if any([offer.lower() in uttr_lower for offer in TOPIC_NEWS_OFFER]):
        return True
    return False


def get_news_about_topic(
    topic: str, NEWS_API_ANNOTATOR_URL: str, discussed_news=None, return_list_of_news=False, timeout_value=1.0
):
    """
    Function to get news output from news-api-skill.
    ```
    import os

    NEWS_API_ANNOTATOR_URL = os.environ.get('NEWS_API_ANNOTATOR_URL')
    result = get_news_about_topic("politics", NEWS_API_ANNOTATOR_URL)
    result = [text, conf, human_attributes, bot_attributes, attributes]
    ```
        attributes contains `curr_news` dictionary with info about news

    Attributes:
        - topic: string topic/entity about which one wants to get news
        - NEWS_API_ANNOTATOR_URL: news api skill url
        - discussed_news: list of string news urls which were given to user (not to repeat)
        - get_list_of_news: whether to get list of news or not

    Returns:
        - dictionary with news, as curr_news about in example
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
    if discussed_news is None:
        discussed_news = []

    human_attr = {"news_api_skill": {"discussed_news": discussed_news}}
    result_news = {}
    dialogs = {
        "dialogs": [
            {
                "utterances": [],
                "bot_utterances": [],
                "human": {"attributes": human_attr},
                "human_utterances": [
                    {
                        "text": f"news about {topic}",
                        "annotations": {"ner": [[{"text": topic}]], "cobot_topics": {"text": ["News"]}},
                    }
                ],
            }
        ],
        "return_list_of_news": return_list_of_news,
    }
    try:
        result = requests.post(NEWS_API_ANNOTATOR_URL, json=dialogs, timeout=timeout_value)
        result = result.json()[0]
        for entity_news_dict in result:
            if entity_news_dict and str(entity_news_dict["entity"]).lower() == topic.lower():
                if return_list_of_news:
                    result_news = entity_news_dict["list_of_news"]
                else:
                    result_news = entity_news_dict["news"]

    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)

    return result_news


BANNED_UNIGRAMS = ["I", "i", "news", "something", "anything", "me"]


def extract_topics(curr_uttr):
    """Extract entities as topics for news request. If no entities found, extract nounphrases.

    Args:
        curr_uttr: current human utterance dictionary

    Returns:
        list of mentioned entities/nounphrases
    """
    entities = get_entities(curr_uttr, only_named=True, with_labels=False)
    entities = [ent.lower() for ent in entities]
    entities = [
        ent
        for ent in entities
        if not (ent == "alexa" and curr_uttr["text"].lower()[:5] == "alexa") and "news" not in ent
    ]
    if len(entities) == 0:
        for ent in get_entities(curr_uttr, only_named=False, with_labels=False):
            if ent.lower() not in BANNED_UNIGRAMS and "news" not in ent.lower():
                if ent in entities:
                    pass
                else:
                    entities.append(ent)
    entities = [ent for ent in entities if len(ent) > 0]
    return entities
