import logging
import requests
import time
from os import getenv

import sentry_sdk

sentry_sdk.init(getenv('SENTRY_DSN'))

DEBUG_MODE = False
if DEBUG_MODE:
    API_KEY = 'QFPxaMUoPi5qcax2FBt9D6Y6vAgLRBbn56TW1iO3'
    QA_SERVICE_URL = 'https://06421kpunk.execute-api.us-east-1.amazonaws.com/prod/qa/v1/answer'
    WIKIDATA_URL = 'http://0.0.0.0:8077/model'
    ENTITY_LINKING_URL = 'http://0.0.0.0:8075/model'
else:
    COBOT_QA_SERVICE_URL = getenv('COBOT_QA_SERVICE_URL')
    WIKIDATA_URL = getenv("WIKIDATA_URL")
    ENTITY_LINKING_URL = getenv("ENTITY_LINKING_URL")
    COBOT_API_KEY = getenv('COBOT_API_KEY')
    assert WIKIDATA_URL and ENTITY_LINKING_URL


def request_entities_entitylinking(entity, types, return_raw=False,
                                   confidence_threshold=0.6):
    """

    Args:
        entity: name of entity we request from entity linking
        types: types we assume this entity has
        return_raw: if True return raw json. Otherwise return entities with probs filtered by confidence
        confidence_threshold: if we filter by confidence declares the confidence above which we keep entities

    Returns:

    """
    logging.debug(f'Calling request_entities for {entity} {types}')
    try:
        assert isinstance(entity, str)
        t = time.time()
        response = requests.post(ENTITY_LINKING_URL,
                                 json={"entity_substr": [[entity]],
                                       "template_found": [""],
                                       "context": [""],
                                       "entity_types": [[types]]},
                                 timeout=1).json()
        exec_time = time.time() - t
        logging.debug(f'Response from entity_linking {response} obtained with exec time  {exec_time:.2f}')
        if return_raw:
            return response
        entities = response[0][0][0]
        probs = response[0][1][0]
        assert len(entities) == len(probs) and entities, response
        entities_with_conf = [(entity, conf)
                              for entity, conf in zip(entities, probs)
                              if conf > confidence_threshold]
        if entities_with_conf:
            entities, probs = zip(*entities_with_conf)
        else:
            entities, probs = [], []
        assert len(entities) == len(probs)
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logging.exception(e)
        entities = []
        probs = []
    return entities, probs


def request_triples_wikidata(parser_info, queries, query_dict={}):
    """

    Args:
        parser_info: parser_info for Wikidata REST API
        queries: queries to Wikidata REST API

    Returns:
        response - response from wikidata REST API if we received it, empty list otherwise
    """
    # logging.info(f"Calling get_triples, parser_info {parser_info}, queries {queries}")
    responses = []
    resp = None
    try:
        t = time.time()
        for query in queries:
            if (parser_info, query) in query_dict:
                curr_response = (query_dict[(parser_info, query)])
            else:
                resp = requests.post(WIKIDATA_URL,
                                     json={"query": [query], "parser_info": [parser_info]},
                                     timeout=1)
                if resp.status_code == 200:
                    curr_response = resp.json()
            if isinstance(curr_response, list):
                responses.extend(curr_response)
            else:
                responses.append(curr_response)
        exec_time = time.time() - t
        logging.info(f'Response from wiki_parser {responses} obtained with exec time  {exec_time:.2f}')
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logging.exception(f'Exception in request_triples_wikidata for {parser_info} {query} answer {resp}')

    return responses
