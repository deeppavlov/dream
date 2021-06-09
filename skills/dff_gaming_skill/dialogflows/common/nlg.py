import logging
import os

import sentry_sdk

import common.constants as common_constants
import common.dialogflow_framework.utils.state as state_utils
import common.gaming as common_gaming

import dialogflows.common.shared_memory_ops as gaming_memory


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))

logger = logging.getLogger(__name__)


CONF_1 = 1.0
CONF_092_CAN_CONTINUE = 0.92
CONF_09_DONT_UNDERSTAND_DONE = 0.9
CONF_0 = 0.0


def error_response(vars):
    logger.info("exec error_response")
    state_utils.set_confidence(vars, 0)
    return "Sorry"


def error_handler(f):
    def wrapper(*args, **kwargs):
        try:
            response = f(*args, **kwargs)
        except Exception as exc:
            logger.exception(exc)
            sentry_sdk.capture_exception(exc)
            if args:
                vars = args[0]
            else:
                vars = kwargs["vars"]
            response = error_response(vars)
        return response
    return wrapper


def get_theme_and_genre_groups(themes, genres):
    themes = set(themes)
    genres = set(genres)
    groups = []
    for group, genres_and_themes in common_gaming.genre_and_theme_groups.items():
        if genres & set(genres_and_themes['genres']) or themes & set(genres_and_themes['themes']):
            groups.append(group)
    return groups


def get_all_relevant_linkto_responses_based_on_genres_and_themes(vars):
    game = gaming_memory.get_current_igdb_game(vars, assert_not_empty=False)
    candidate_responses = []
    if game:
        themes, genres = game.get("themes", []), game.get("genres", [])
        theme_and_genre_groups = get_theme_and_genre_groups(themes, genres)
        for skill_links in [common_gaming.links_to_movies, common_gaming.links_to_books]:
            for theme in themes:
                candidate_responses += skill_links["theme"].get(theme, [])
            for group in theme_and_genre_groups:
                candidate_responses += skill_links["theme_genre_group"].get(group, [])
    return candidate_responses


def get_new_linkto_response_based_on_genres_and_themes(vars):
    linkto_responses_based_on_genres_and_themes = get_all_relevant_linkto_responses_based_on_genres_and_themes(vars)
    result = None
    if linkto_responses_based_on_genres_and_themes:
        used_linkto_phrases_ids = gaming_memory.get_used_linkto_phrase_ids(vars)
        for response in linkto_responses_based_on_genres_and_themes:
            id_ = gaming_memory.LINKTO_RESPONSES_TO_LINKTO_IDS.get(response)
            assert id_ is not None, f"Link phrases added to shared memory has to be from `common.gaming`. "\
                f"Got: '{response}'"
            if id_ not in used_linkto_phrases_ids:
                result = response
                break
    return result


@error_handler
def link_to_other_skills_response(vars, prefix="Okay.", shared_memory_actions=None):
    response = get_new_linkto_response_based_on_genres_and_themes(vars)
    if response is None:
        response = ""
        state_utils.set_confidence(vars, confidence=CONF_0)
    else:
        response = ' '.join([prefix, response])
        state_utils.set_confidence(vars, confidence=CONF_09_DONT_UNDERSTAND_DONE)
    if shared_memory_actions is not None:
        for action in shared_memory_actions:
            action(vars)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_NOT_CONTINUE)
    return response
