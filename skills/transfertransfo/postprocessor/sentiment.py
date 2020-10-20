import logging
import os
import json

import requests
import numpy as np

# import emoji
import sentry_sdk

SENTRY_DSN = os.getenv("SENTRY_DSN")
SENTIMENT_CLASSIFICATION_SERVICE_URL = os.getenv(
    "SENTIMENT_CLASSIFICATION_SERVICE_URL", "http://sentiment_classification:8024/model"
)

sentry_sdk.init(SENTRY_DSN)
logger = logging.getLogger(__name__)


def get_sentiment(text):
    """
    Returns:
    (sentiment, confidens) (str, float): sentiment and confidence
    """
    try:
        sentiment_result = requests.request(
            url=SENTIMENT_CLASSIFICATION_SERVICE_URL,
            data=json.dumps({"sentences": [text]}),
            method="POST",
            timeout=10
        )
    except (requests.ConnectTimeout, requests.ReadTimeout) as e:
        sentry_sdk.capture_exception(e)
        logger.exception("SentumentResult Timeout")
        sentiment_result = requests.Response()
        sentiment_result.status_code = 504

    if sentiment_result.status_code != 200:
        msg = "Sentiment classifier: result status code is not 200: {}. result text: {}; result status: {}".format(
            sentiment_result, sentiment_result.text, sentiment_result.status_code
        )
        sentry_sdk.capture_message(msg)
        logger.warning(msg)
        sentiment = ["neutral", 1]
    else:
        sentiment = sentiment_result.json()[0][0]

    return sentiment


def pick_emoji(text):
    smiles = {
        "positive": [
            " it pleases me",
            " it delights me",
            " it makes my soul warmer",
            " it's great and it seems that the world is getting a little better",
            " nice to know that",
        ],
        "negative": [" from this restless at heart", " so sad to me", " sadly", " sad to think about it"],
    }

    # l_pos = "positive"
    # l_neg = "negative"
    l_neut = "neutral"

    sentiment = get_sentiment(text)[0]

    if sentiment == l_neut:
        return ""

    return np.random.choice(smiles[sentiment])
