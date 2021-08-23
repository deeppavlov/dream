# %%
import os
import logging

import requests

import sentry_sdk

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))


ENTITY_LINKING_URL = os.getenv("ENTITY_LINKING_URL")
WIKIDATA_URL = os.getenv("WIKIDATA_URL")
assert ENTITY_LINKING_URL, ENTITY_LINKING_URL
assert WIKIDATA_URL, WIKIDATA_URL


logger = logging.getLogger(__name__)

TOP_NUMBER = 3


def get_genre_top_wiki_parser(category, genre):
    top = []
    wp_output = []
    wp_output = requests.post(
        WIKIDATA_URL,
        json={
            "parser_info": ["find_topic_info"],
            "query": [{"category": category, "genre": genre}]
        },
    ).json()

    if wp_output:
        top = wp_output[:TOP_NUMBER]
    return top


def get_team_players_top_wiki_parser(team, utterance):
    top = []
    entity_id = ""
    wp_output = []
    try:
        el_output = requests.post(
            ENTITY_LINKING_URL,
            json={"entity_substr": [[team]], "template": [""], "context": [utterance]},
            timeout=0.8,
        ).json()

        entity_info = el_output and el_output[0] and el_output[0][0]
        if isinstance(entity_info, list) and entity_info and entity_info[0]:
            entity_ids = entity_info[0]
            entity_id = entity_ids[0]
            wp_output = requests.post(
                WIKIDATA_URL,
                json={"parser_info": ["find_object"], "query": [(entity_id, "P54", "backw")]},
                timeout=0.8,
            ).json()
        elif isinstance(entity_info, dict):
            entity_ids = entity_info.get("entity_ids", [])
            entity_id = entity_ids and entity_ids[0]
            wp_output = (
                entity_id
                and requests.post(
                    WIKIDATA_URL,
                    json={"parser_info": ["find_object"], "query": [(entity_id, "P54", "backw")]},
                    timeout=0.8,
                ).json()
            )
            logger.info(f"get_team_players_top_wiki_parser: wp_input: entity_substr: {team},"
                        f"subject: {entity_id}, wp_output = {wp_output}")

        top = [i[1] for i in wp_output[0][0][:TOP_NUMBER]] if wp_output[0] else []
    except Exception as exc:
        msg = f"request_team_players_el_wp_entities exception: {exc}"
        logger.warning(msg)
        sentry_sdk.capture_message(msg)
    return top


def get_object_top_wiki_parser(item, objects, category, utterance):
    top = []
    entity_id = ""
    wp_output = []
    try:
        el_output = requests.post(
            ENTITY_LINKING_URL,
            json={"entity_substr": [[item]], "template": [""], "context": [utterance]},
            timeout=0.8,
        ).json()

        entity_info = el_output and el_output[0] and el_output[0][0]
        if isinstance(entity_info, list) and entity_info and entity_info[0]:
            entity_ids = entity_info[0]
            entity_id = entity_ids[0]
            wp_output = requests.post(
                WIKIDATA_URL,
                json={"parser_info": ["find_topic_info"], "query": [
                    {"what_to_find": objects, "category": category, "subject": entity_id}
                ]},
                timeout=0.8,
            ).json()
        elif isinstance(entity_info, dict):
            entity_ids = entity_info.get("entity_ids", [])
            entity_id = entity_ids and entity_ids[0]
            wp_output = (
                entity_id
                and requests.post(
                    WIKIDATA_URL,
                    json={"parser_info": ["find_topic_info"], "query": [
                        {"what_to_find": objects, "category": category, "subject": entity_id}
                    ]},
                    timeout=0.8,
                ).json()
            )
            logger.info(f"get_object_top_wiki_parser: wp_input: what_to_find: {objects},"
                        f"category: {category}, subject: {entity_id}, wp_output = {wp_output}")

        top = [i[1] for i in wp_output[0][0][:TOP_NUMBER]] if wp_output[0] else []
    except Exception as exc:
        msg = f"request_el_wp_entities exception: {exc}"
        logger.warning(msg)
        sentry_sdk.capture_message(msg)
    return top
