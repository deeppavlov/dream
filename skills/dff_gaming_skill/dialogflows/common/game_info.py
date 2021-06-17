import logging
import os

import requests
import sentry_sdk
from requests import RequestException

import common.dialogflow_framework.utils.state as state_utils
from common.gaming import GAMES_WITH_AT_LEAST_1M_COPIES_SOLD_COMPILED_PATTERN, VIDEO_GAME_WORDS_COMPILED_PATTERN,\
    load_json


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))

logger = logging.getLogger(__name__)


games_igdb_search_results = load_json(os.getenv("GAMES_IGDB_SEARCH_RESULTS"))
games_igdb_ids = load_json(os.getenv('GAMES_IGDB_IDS'))


CLIENT_ID = os.getenv("TWITCH_IGDB_CLIENT_ID")
CLIENT_SECRET = os.getenv("TWITCH_IGDB_CLIENT_SECRET")


def get_igdb_client_token():
    payload = {"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "grant_type": "client_credentials"}
    url = "https://id.twitch.tv/oauth2/token?"
    timeout = 20.0
    try:
        token_data = requests.post(url, params=payload, timeout=timeout)
    except RequestException as e:
        logger.warning(f"Request to {url} failed. `dff_gaming_skill` failed to get access to igdb.com. {e}")
        access_token = None
    else:
        token_data_json = token_data.json()
        access_token = token_data_json.get("access_token")
        if access_token is None:
            logger.warning(
                f"Could not get access token for CLIENT_ID={CLIENT_ID} and CLIENT_SECRET={CLIENT_SECRET}. "
                f"`dff_gaming_skill` failed to get access to igdb.com\n"
                f"payload={payload}\nurl={url}\ntimeout={timeout}\nresponse status code: {token_data.status_code}"
            )
    return access_token


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["Authorization"] = "Bearer " + self.token
        return r


CLIENT_TOKEN = get_igdb_client_token()
logger.info(f"CLIENT_TOKEN={CLIENT_TOKEN}")
if CLIENT_TOKEN is None:
    IGDB_POST_KWARGS = None
else:
    IGDB_POST_KWARGS = {
        "auth": BearerAuth(CLIENT_TOKEN),
        "headers": {"Client-ID": CLIENT_ID, "Accept": "application/json", "Content-Type": "text/plain"},
        "timeout": 1.0,
    }


def get_game_description_for_first_igdb_candidate(name, results_sort_key):
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
        name,
        results_sort_key="rating_count",
        search_result_keys_to_keep=(
            "url", "rating", "rating_count", "summary", "created_at", "first_release_date", "involved_companies",
            "genres", "themes", "category", "name", "id"),
):
    logger.info(f"Searching for igdb game description of game {repr(name)}")
    igdb_game_description = get_game_description_for_first_igdb_candidate(name, results_sort_key)
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
    user_uttr = state_utils.get_last_human_utterance(vars)
    prev_bot_uttr = state_utils.get_last_bot_utterance(vars)
    game_names_from_local_list_of_games = GAMES_WITH_AT_LEAST_1M_COPIES_SOLD_COMPILED_PATTERN.findall(
        user_uttr.get("text", "")) \
        + GAMES_WITH_AT_LEAST_1M_COPIES_SOLD_COMPILED_PATTERN.findall(prev_bot_uttr.get("text", ""))
    assert game_names_from_local_list_of_games, \
        "At least one game should have been found in function `switch_to_particular_game_discussion()`"
    first_name = game_names_from_local_list_of_games[0]
    match = VIDEO_GAME_WORDS_COMPILED_PATTERN.match(first_name)
    if match:
        game_word_mentioned = True
        first_name = first_name[match.span()[1]:]
    else:
        game_word_mentioned = False
    return search_igdb_for_game(first_name), game_word_mentioned
