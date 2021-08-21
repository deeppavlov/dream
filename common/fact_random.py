import json
import logging
from os import getenv

import requests
import sentry_sdk


sentry_sdk.init(getenv('SENTRY_DSN'))
logger = logging.getLogger(__name__)


FACT_RANDOM_SERVICE_URL = getenv('FACT_RANDOM_SERVICE_URL')
if FACT_RANDOM_SERVICE_URL is None:
    raise RuntimeError('FACT_RANDOM_SERVICE_URL environment variable is not set')
HEADERS = {'Content-Type': 'application/json;charset=utf-8'}
TIMEOUT = 0.9


def load_fact_file(path):
    with open(path, "r") as f:
        facts = json.load(f)
    for fact_key in list(facts.keys()):
        facts[fact_key.lower()] = facts.pop(fact_key)
    return facts


def get_facts(question):
    """
    Interface method of fact-random service
    :param question: string with question in Natural Language
    :return: answer as string in natural language
    """
    request_body = {'question': question}
    try:
        resp = requests.request(url=FACT_RANDOM_SERVICE_URL,
                                headers=HEADERS,
                                data=json.dumps(request_body),
                                method='POST',
                                timeout=TIMEOUT)
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
        resp = requests.Response()
        resp.status_code = 504

    if resp.status_code != 200:
        logger.warning(
            f"result status code is not 200: {resp}. result text: {resp.text}; "
            f"result status: {resp.status_code}")
        response = ''
        sentry_sdk.capture_message(
            f"CobotQA! result status code is not 200: {resp}. result text: {resp.text}; "
            f"result status: {resp.status_code}")
    else:
        response = resp.json()['response']

    return response
