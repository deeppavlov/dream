import logging
import os
import json
import requests
import pathlib
from copy import deepcopy
from os import getenv
import sentry_sdk

sentry_sdk.init(getenv('SENTRY_DSN'))
logger = logging.getLogger(__name__)

COBOT_API_KEY = os.environ.get('COBOT_API_KEY')
COBOT_QA_SERVICE_URL = os.environ.get('COBOT_QA_SERVICE_URL')

if COBOT_API_KEY is None:
    raise RuntimeError('COBOT_API_KEY environment variable is not set')
if COBOT_QA_SERVICE_URL is None:
    raise RuntimeError('COBOT_QA_SERVICE_URL environment variable is not set')

headers = {'Content-Type': 'application/json;charset=utf-8', 'x-api-key': f'{COBOT_API_KEY}'}

# travel
with open(pathlib.Path(__file__).resolve().parent / "facts_for_cities.json", "r") as f:
    TRAVEL_FACTS = json.load(f)
with open(pathlib.Path(__file__).resolve().parent / "facts_for_countries.json", "r") as f:
    data = json.load(f)
    for name in data:
        TRAVEL_FACTS[name] = deepcopy(data[name])
TRAVEL_FACTS = {name.lower(): fact for name, fact in TRAVEL_FACTS.items()}
# food
with open(pathlib.Path(__file__).resolve().parent / "food_facts.json", "r") as f:
    FOOD_FACTS = json.load(f)
FOOD_FACTS = {name.lower(): fact for name, fact in FOOD_FACTS.items()}
# animals
with open(pathlib.Path(__file__).resolve().parent / "facts_for_animals.json", "r") as f:
    ANIMALS_FACTS = json.load(f)
ANIMALS_FACTS = {name.lower(): fact for name, fact in ANIMALS_FACTS.items()}


def send_cobotqa(question):
    """
    Interface method of the CoBotQA
    :param question: string with question in Natural Language
    :return: answer as string in natural language
    """
    request_body = {'question': question}
    try:
        resp = requests.request(url=COBOT_QA_SERVICE_URL,
                                headers=headers,
                                data=json.dumps(request_body),
                                method='POST',
                                timeout=0.9)
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
