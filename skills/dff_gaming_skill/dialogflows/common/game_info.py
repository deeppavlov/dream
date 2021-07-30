import logging
import os

import requests
import sentry_sdk
from requests import RequestException

import common.dialogflow_framework.utils.state as state_utils
from common.gaming import CHECK_DEFINITELY_GAME_COMPILED_PATTERN, get_igdb_client_token, get_igdb_post_kwargs, \
    load_json, find_games_in_text


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))

logger = logging.getLogger(__name__)


games_igdb_search_results = load_json(os.getenv("GAMES_IGDB_SEARCH_RESULTS"))
games_igdb_ids = load_json(os.getenv('GAMES_IGDB_IDS'))


CLIENT_ID = os.getenv("TWITCH_IGDB_CLIENT_ID")
CLIENT_SECRET = os.getenv("TWITCH_IGDB_CLIENT_SECRET")


CLIENT_TOKEN = get_igdb_client_token(CLIENT_ID, CLIENT_SECRET)
logger.info(f"CLIENT_TOKEN={CLIENT_TOKEN}")
if CLIENT_TOKEN is None:
    IGDB_POST_KWARGS = None
else:
    IGDB_POST_KWARGS = get_igdb_post_kwargs(CLIENT_TOKEN, CLIENT_ID)


def does_text_contain_video_game_words(text):
    flag = bool(CHECK_DEFINITELY_GAME_COMPILED_PATTERN.search(text))
    logger.info(f"does_text_contain_video_game_words={flag}")
    return flag


def get_game_description_for_first_igdb_candidate(match_names, results_sort_key):
    name = match_names[0]
    name_lower = name.lower()
    if isinstance(results_sort_key, str):
        def results_sort_key(x):
            return -x[results_sort_key] if results_sort_key in x else 1
    elif not callable(results_sort_key):
        raise ValueError("The argument `results_sort_key` has to be either `str` or callable.")
    if name_lower in games_igdb_search_results:
        igdb_game_description = games_igdb_search_results.get(name_lower)
        logger.info(f"found saved search results for game query '{name}'. Game description: {igdb_game_description}")
    elif IGDB_POST_KWARGS is not None:
        search_body = f'search "{name}"; fields *; where themes != (42);'  # 42 is 'Erotic'
        try:
            logger.info(f"making request to https://api.igdb.com/v4/games. Search body: {search_body}")
            search_results = requests.post(
                "https://api.igdb.com/v4/games",
                data=search_body,
                **IGDB_POST_KWARGS,
            )
        except RequestException as e:
            logger.warning(e)
            search_results = []
        if search_results:
            igdb_game_description = sorted(search_results.json(), key=results_sort_key)[0]
        else:
            if not isinstance(search_results, list):
                logger.warning(
                    f"ERROR while posting search for game '{name}' to https://api.igdb.com/v4/games. "
                    f"ERROR {search_results.status_code}: {search_results.reason}"
                )
            igdb_game_description = None
        if igdb_game_description is not None:
            games_igdb_search_results[name_lower] = igdb_game_description
            games_igdb_ids[str(igdb_game_description["id"])] = igdb_game_description
            logger.info(
                f"Found game descriptions for query '{name}' on igdb.com. Selected game description: "
                f"{igdb_game_description}"
            )
    else:
        logger.warning("Could not get access (client) token for igdb.com so only saved game descriptions are available")
        igdb_game_description = None
    return igdb_game_description


def search_igdb_for_game(
        match_names,
        results_sort_key="rating_count",
        search_result_keys_to_keep=(
            "url", "rating", "rating_count", "summary", "created_at", "first_release_date", "involved_companies",
            "genres", "themes", "category", "name", "id"),
):
    logger.info(f"Searching for igdb game description of game {repr(match_names)}")
    igdb_game_description = get_game_description_for_first_igdb_candidate(match_names, results_sort_key)
    if igdb_game_description is not None:
        filtered_game_description = {}
        game_description_lacks_required_keys = False
        for k in search_result_keys_to_keep:
            if k in igdb_game_description:
                filtered_game_description[k] = igdb_game_description[k]
            else:
                name_str = f" '{igdb_game_description['name']}'" if 'name' in igdb_game_description else ""
                logger.warning(
                    f"Required key '{k}' is missing in information about game{name_str}. "
                    f"Game info: {igdb_game_description}. Skipping..."
                )
                game_description_lacks_required_keys = True
                break
        if game_description_lacks_required_keys:
            filtered_game_description = None
    else:
        filtered_game_description = None
    if filtered_game_description is not None:
        logger.info(f"Filtered game description: {filtered_game_description}")
    return filtered_game_description


def search_igdb_game_description_by_user_and_bot_phrases(vars):
    user_text = state_utils.get_last_human_utterance(vars).get("text", "").lower()
    prev_bot_text = state_utils.get_last_bot_utterance(vars).get("text", "").lower()
    game_names_from_local_list_of_games = find_games_in_text(user_text) + find_games_in_text(prev_bot_text)
    assert game_names_from_local_list_of_games, \
        "At least one game should have been found in function `switch_to_particular_game_discussion()`"
    first_match_names = game_names_from_local_list_of_games[0]
    game_word_mentioned = does_text_contain_video_game_words(user_text) \
        or does_text_contain_video_game_words(prev_bot_text)
    return search_igdb_for_game(first_match_names), game_word_mentioned
