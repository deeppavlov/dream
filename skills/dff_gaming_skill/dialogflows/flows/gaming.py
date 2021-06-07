# %%
import inspect
import json
import logging
import os
from functools import partial
from enum import Enum, auto

import sentry_sdk
import requests
from nltk.tokenize import sent_tokenize
from requests.exceptions import RequestException

import common.constants as common_constants
import common.dialogflow_framework.stdm.dialogflow_extention as dialogflow_extention
import common.dialogflow_framework.utils.state as state_utils
import common.gaming as common_gaming
from common.gaming import GAMES_WITH_AT_LEAST_1M_COPIES_SOLD_COMPILED_PATTERN, VIDEO_GAME_WORDS_COMPILED_PATTERN,\
    load_json
from common.universal_templates import if_chat_about_particular_topic, if_choose_topic
from common.utils import is_yes

import dialogflows.scopes as scopes


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))

logger = logging.getLogger(__name__)


CONF_1 = 1.0
CONF_092_CAN_CONTINUE = 0.92
CONF_09_DONT_UNDERSTAND_DONE = 0.9
CONF_0 = 0.0

NUM_SENTENCES_IN_ONE_TURN_OF_GAME_DESCRIPTION = 2


CLIENT_ID = os.getenv("TWITCH_IGDB_CLIENT_ID")
CLIENT_SECRET = os.getenv("TWITCH_IGDB_CLIENT_SECRET")


ASSERTION_ERROR_NO_GAMES_IN_SHARED_MEMORY = "Shared memory field 'igdb_game_ids_user_wanted_to_discuss' is empty. "\
    "If dff_gaming_skill reached state SYS_USER_CONFIRMS_GAME 'games_user_wanted_do_discuss' cannot be empty "
ASSERTION_ERROR_MSG_CANDIDATE_IS_GAME_NOT_SET = "This function should be called if shared memory field "\
    "`candidate_game_id` is set. Shared memory field 'candidate_game_id' is supposed to be set when skill goes "\
    "through states SYS_USER_MAYBE_WANTS_TO_TALK_ABOUT_PARTICULAR_GAME -> USR_CHECK_WITH_USER_GAME_TITLE and "\
    "the field is supposed to be emptied when skill leaves states SYS_USER_CONFIRMS_GAME_BOT_NEVER_PLAYED, "\
    "SYS_USER_CONFIRMS_MINECRAFT, SYS_USER_CONFIRMS_GAME_BOT_NEVER_PLAYED."


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
            response = error_response(*args, **kwargs)
        return response
    return wrapper


def get_igdb_client_token():
    payload = {"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "grant_type": "client_credentials"}
    url = "https://id.twitch.tv/oauth2/token?"
    timeout = 20.0
    try:
        token_data = requests.post(url, params=payload, timeout=timeout)
    except RequestException as e:
        logger.warning(f"Request to {url} failed. `dff_gaming_skill` failed to build. {e}")
        access_token = None
    else:
        token_data_json = token_data.json()
        access_token = token_data_json.get("access_token")
        if access_token is None:
            logger.warning(
                f"Could not get access token for CLIENT_ID={CLIENT_ID} and CLIENT_SECRET={CLIENT_SECRET}. "
                f"`dff_gaming_skill` failed to build\n"
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
if CLIENT_TOKEN is None:
    IGDB_POST_KWARGS = {
        "auth": BearerAuth(CLIENT_TOKEN),
        "headers": {"Client-ID": CLIENT_ID, "Accept": "application/json", "Content-Type": "text/plain"},
        "timeout": 1.0,
    }
else:
    IGDB_POST_KWARGS = None


def get_book_genres():
    with open(os.getenv("BOOKREADS_DATA")) as f:
        data = json.load(f)
    genres = list(data[0].keys())
    return genres


def get_imdb_movie_genres():
    with open(os.getenv("IMDB_MOVIE_GENRES")) as f:
        genres = json.load(f)
    return genres


def get_igdb_id_to_name(field, name_key):
    if field == "theme":
        env_name = "IGDB_GAME_THEMES"
    elif field == "genre":
        env_name = "IGDB_GAME_GENRES"
    else:
        raise ValueError(f"The only supported `field` argument values are 'theme' and 'genre'. Got '{field}'")
    with open(os.getenv(env_name)) as f:
        data = json.load(f)
    res = {}
    for d in data:
        id_ = d.get("id")
        name = d.get(name_key)
        if id_ is None or name is None:
            raise ValueError(f"Game description has to have both 'name' and 'id' fields. Got game description: {d}")
        res[id_] = name
    return res


def build_linkto_responses_to_ids_dictionary(
        movies_linktos_based_on_themes_and_genres,
        books_linktos_based_on_themes_and_genres,
        movies_special_linktos,
        books_special_linktos,
):
    res = {}
    count = 0
    for to_skill_responses in [movies_linktos_based_on_themes_and_genres, books_linktos_based_on_themes_and_genres]:
        for based_on_responses in to_skill_responses.values():
            for responses in based_on_responses.values():
                for r in responses:
                    res[r] = count
                    count += 1
    for to_skill_responses in [movies_special_linktos, books_special_linktos]:
        for responses in to_skill_responses.values():
            for r in responses:
                res[r] = count
                count += 1
    return res


##################################################################################################################
# Load Data
##################################################################################################################

BOOK_GENRES = get_book_genres()
IMDB_MOVIE_GENRES = get_imdb_movie_genres()
IGDB_GAME_GENRES_FOR_REPLICAS = get_igdb_id_to_name('genre', "name_for_inserting_into_replica")
IGDB_GAME_THEMES = get_igdb_id_to_name('theme', "name")
LINKTO_RESPONSES_TO_LINKTO_IDS = build_linkto_responses_to_ids_dictionary(
    common_gaming.links_to_movies,
    common_gaming.links_to_books,
    common_gaming.special_links_to_movies,
    common_gaming.special_links_to_books
)


def load_lines_from_text_file(file_name):
    with open(file_name) as f:
        lines = [line.strip() for line in f.readlines()]
    return lines


# new search results may be appended
games_igdb_search_results = load_json(os.getenv("GAMES_IGDB_SEARCH_RESULTS"))
games_igdb_ids = load_json(os.getenv('GAMES_IGDB_IDS'))


class State(Enum):
    USR_START = auto()
    ####################
    SYS_USER_MAYBE_WANTS_TO_TALK_ABOUT_PARTICULAR_GAME = auto()
    SYS_USER_DEFINITELY_WANTS_TO_TALK_ABOUT_GAME_BOT_NEVER_PLAYED = auto()
    SYS_USER_DEFINITELY_WANTS_TO_TALK_ABOUT_MINECRAFT = auto()
    # from SYS_USER_WANTS_TO_TALK_ABOUT_PARTICULAR_GAME
    USR_CHECK_WITH_USER_GAME_TITLE = auto()

    # from USR_CHECK_WITH_USER_GAME_TITLE
    SYS_USER_CONFIRMS_GAME_BOT_NEVER_PLAYED = auto()
    SYS_USER_CONFIRMS_MINECRAFT = auto()
    SYS_USER_DOESNT_CONFIRM_GAME = auto()

    # from SYS_USER_CONFIRMS_GAME_BOT_NEVER_PLAYED
    USR_CONFESS_BOT_NEVER_PLAYED_GAME_ASK_USER_IF_HE_PLAYED = auto()

    # from SYS_USER_CONFIRMS_MINECRAFT
    USR_TELL_ABOUT_BUILDING_HOGWARTS_IN_MINECRAFT_ASK_WHAT_INTERESTING_USER_BUILT = auto()

    # from USR_TELL_ABOUT_BUILDING_HOGWARTS_IN_MINECRAFT_ASK_WHAT_INTERESTING_USER_BUILT
    SYS_USER_TELLS_ABOUT_HIS_ACHIEVEMENT_IN_MINECRAFT = auto()

    # from USR_ASK_USER_IF_HE_PLAYED_GAME
    SYS_USER_PLAYED_GAME = auto()
    SYS_USER_DIDNT_PLAY_GAME = auto()

    # from SYS_USER_PLAYED_GAME
    USR_TELL_ABOUT_WHAT_BOT_LIKES_AND_ASK_IF_USER_RECOMMENDS_GAME = auto()

    # from USR_TELL_ABOUT_WHAT_BOT_LIKES_AND_ASK_IF_USER_RECOMMENDS_GAME
    SYS_USER_RECOMMENDS_GAME = auto()
    SYS_USER_DOESNT_RECOMMEND_GAME = auto()

    # from SYS_USER_DIDNT_PLAY_GAME
    USR_SUGGEST_USER_GAME_DESCRIPTION = auto()

    # from USR_SUGGEST_USER_GAME_DESCRIPTION
    SYS_USER_WANTS_GAME_DESCRIPTION_AND_2_OR_MORE_TURNS_OF_DESCRIPTION_REMAIN = auto()
    SYS_USER_WANTS_GAME_DESCRIPTION_LAST_TURN_OF_DESCRIPTION = auto()
    SYS_USER_DOESNT_WANT_GAME_DESCRIPTION = auto()

    # from SYS_USER_WANTS_GAME_DESCRIPTION_AND_2_OR_MORE_TURNS_OF_DESCRIPTION_REMAIN
    USR_DESCRIBE_GAME_TO_USER_AND_ASK_IF_HE_WANTS_MORE = auto()

    # from SYS_USER_WANTS_GAME_DESCRIPTION_LAST_TURN_OF_DESCRIPTION
    USR_DESCRIBE_GAME_TO_USER_AND_ASK_HE_WANTS_TO_PLAY_GAME = auto()

    # from USR_DESCRIBE_GAME_TO_USER_AND_ASK_HE_WANTS_TO_PLAY_GAME
    SYS_USER_SAYS_HE_WANTS_TO_PLAY_GAME = auto()
    SYS_USER_SAYS_HE_DOESNT_WANT_TO_PLAY_GAME = auto()

    ####################
    SYS_ERR = auto()
    USR_ERR = auto()


def lets_talk_about_game(vars):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    # have_pets = re.search(HAVE_LIKE_PETS_TEMPLATE, user_uttr["text"])
    # found_prompt = any([phrase in bot_uttr for phrase in TRIGGER_PHRASES])
    # isyes = is_yes(user_uttr)
    chat_about = if_chat_about_particular_topic(
        user_uttr,
        bot_uttr,
        compiled_pattern=GAMES_WITH_AT_LEAST_1M_COPIES_SOLD_COMPILED_PATTERN
    )
    if chat_about:
        flag = True
    return flag


def switch_to_particular_game_discussion(vars):
    user_uttr = state_utils.get_last_human_utterance(vars)
    prev_bot_uttr = state_utils.get_last_bot_utterance(vars)
    found_video_game_name = bool(
        GAMES_WITH_AT_LEAST_1M_COPIES_SOLD_COMPILED_PATTERN.search(user_uttr.get("text", "").lower()))
    choose_particular_game = if_choose_topic(user_uttr, prev_bot_uttr) and found_video_game_name
    question_answer_contains_video_game = "?" not in user_uttr.get("text", "") \
        and "?" in prev_bot_uttr.get("text", "") \
        and found_video_game_name
    return lets_talk_about_game(vars) or choose_particular_game or question_answer_contains_video_game


def extract_game_names_user_wants_to_discuss_from_re(vars, compiled_regexp):
    user_uttr = state_utils.get_last_human_utterance(vars)
    games = compiled_regexp.findall(user_uttr['text'])
    return games


def get_game_description_for_first_igdb_candidate(name, results_sort_key):
    if isinstance(results_sort_key, str):
        def results_sort_key(x):
            return -x[results_sort_key] if results_sort_key in x else 1
    elif not callable(results_sort_key):
        raise ValueError("The argument `results_sort_key` has to be either `str` or callable.")
    if name in games_igdb_search_results:
        igdb_game_description = games_igdb_search_results.get(name)
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
            games_igdb_search_results[name] = igdb_game_description
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
            "genres", "themes", "category", "name", "alternative_names", "id"),
):
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


def get_igdb_ids_for_games_user_wanted_to_discuss(vars, assert_not_empty=True):
    shared_memory = state_utils.get_shared_memory(vars)
    ids = shared_memory.get("igdb_ids_for_games_user_wanted_to_discuss", [])
    if assert_not_empty:
        assert ids, "Shared memory field 'igdb_game_ids_user_wanted_to_discuss' is empty. If dff_gaming_skill reached "\
            "state SYS_USER_CONFIRMS_GAME 'games_user_wanted_do_discuss' cannot be empty "
    return ids


def get_current_igdb_game(vars, assert_not_empty=True):
    shared_memory = state_utils.get_shared_memory(vars)
    game_id = shared_memory.get("current_igdb_game_id", "")
    if assert_not_empty:
        assert game_id, "Shared memory field 'current_igdb_game_id' is empty. If dff_gaming_skill reached "\
            "state SYS_USER_CONFIRMS_GAME and did not reached SYS_ERR 'current_igdb_game_id' cannot be empty"
    game = games_igdb_ids.get(str(game_id))
    assert game is not None, f"If some game is set for discussion it should have been added to `games_igdb_ids`. "\
        f"No game for id {repr(game_id)}."
    return game


def get_candidate_game_id(vars):
    shared_memory = state_utils.get_shared_memory(vars)
    logger.info(f"(get_candidate_game_id)shared_memory: {shared_memory.keys()}")
    candidate_game_id = shared_memory.get("candidate_game_id")
    return candidate_game_id


def get_theme_and_genre_groups(themes, genres):
    themes = set(themes)
    genres = set(genres)
    groups = []
    for group, genres_and_themes in common_gaming.genre_and_theme_groups.items():
        if genres & set(genres_and_themes['genres']) or themes & set(genres_and_themes['themes']):
            groups.append(group)
    return groups


def get_used_linkto_phrase_ids(vars):
    shared_memory = state_utils.get_shared_memory(vars)
    return shared_memory.get("used_linkto_phrase_ids_from_gaming", [])


def add_used_linkto_to_shared_memory(vars, text):
    used_linkto_phrase_ids = get_used_linkto_phrase_ids(vars)
    id_ = LINKTO_RESPONSES_TO_LINKTO_IDS.get(text)
    assert id_ is not None, f"Link phrases added to shared memory has to be from `common.gaming`. Got: '{text}'"
    used_linkto_phrase_ids.append(id_)
    state_utils.save_to_shared_memory(vars, used_linkto_phrase_ids_from_gaming=used_linkto_phrase_ids)


def get_all_relevant_linkto_responses_based_on_genres_and_themes(vars):
    game = get_current_igdb_game(vars, assert_not_empty=False)
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
        used_linkto_phrases_ids = get_used_linkto_phrase_ids(vars)
        for response in linkto_responses_based_on_genres_and_themes:
            id_ = LINKTO_RESPONSES_TO_LINKTO_IDS.get(response)
            assert id_ is not None, f"Link phrases added to shared memory has to be from `common.gaming`. "\
                f"Got: '{response}'"
            if id_ not in used_linkto_phrases_ids:
                result = response
                break
    return result


def get_split_summary(vars):
    shared_memory = state_utils.get_shared_memory(vars)
    current_index = shared_memory.get("curr_summary_sent_index", "")
    game = get_current_igdb_game(vars)
    summary = game.get('summary')
    assert summary is not None, "Game descriptions without required keys are filtered in function "\
        "`search_igdb_for_game` function. Maybe the wrong list of keys was passed to `search_igdb_for_game`, or "\
        "game description was acquired some other way, or game description was modified."
    sentences = sent_tokenize(summary)
    split_summary = {'sentences': sentences, "current_index": current_index}
    return split_summary


def get_next_sentences_from_summary_and_num_remaining(vars, n_sent=2):
    split_summary = get_split_summary(vars)
    i = split_summary['current_index']
    split_summary = get_split_summary(vars)
    text = ' '.join(split_summary['sentences'][i:i + n_sent])
    split_summary['current_index'] += n_sent
    num_remaining = len(split_summary['sentences']) - split_summary['current_index']
    state_utils.save_to_shared_memory(vars, curr_summary_sent_index=split_summary['current_index'])
    return text, num_remaining


def put_game_id_to_igdb_game_ids_user_wanted_to_discuss(vars, id_):
    ids = get_igdb_ids_for_games_user_wanted_to_discuss(vars, False)
    ids.append(id_)
    state_utils.save_to_shared_memory(vars, igdb_game_ids_user_wanted_to_discuss=ids)


def put_candidate_id_to_igdb_game_ids_user_wanted_to_discuss(vars):
    candidate_game_id = get_candidate_game_id(vars)
    assert candidate_game_id is not None and candidate_game_id, ASSERTION_ERROR_MSG_CANDIDATE_IS_GAME_NOT_SET
    put_game_id_to_igdb_game_ids_user_wanted_to_discuss(vars, candidate_game_id)


def clean_candidate_game_id(vars):
    state_utils.save_to_shared_memory(vars, candidate_game_id="")


def set_current_igdb_game_id_from_candidate_game_id(vars):
    logger.info("set_current_igdb_game_id_from_candidate_game_id")
    candidate_game_id = get_candidate_game_id(vars)
    assert candidate_game_id is not None and candidate_game_id, ASSERTION_ERROR_MSG_CANDIDATE_IS_GAME_NOT_SET
    state_utils.save_to_shared_memory(vars, current_igdb_game_id=candidate_game_id)


def are_there_2_or_more_turns_left_in_game_description(ngrams, vars):
    split_summary = get_split_summary(vars)
    if split_summary:
        num_remaining_sentences = len(split_summary['sentences']) - split_summary['current_index']
        res = num_remaining_sentences / NUM_SENTENCES_IN_ONE_TURN_OF_GAME_DESCRIPTION > 1
    else:
        res = False
    return res


def is_game_candidate_minecraft(ngrams, vars):
    candidate_game_id = get_candidate_game_id(vars)
    assert candidate_game_id is not None and candidate_game_id, ASSERTION_ERROR_MSG_CANDIDATE_IS_GAME_NOT_SET
    candidate_game = games_igdb_ids[candidate_game_id]
    return "minecraft" in candidate_game["name"].lower()


def is_minecraft_mentioned_in_user_uttr(ngrams, vars):
    user_uttr_text = state_utils.get_last_human_utterance(vars)["text"]
    return "minecraft" in user_uttr_text.lower()


def is_found_text_definitely_game(text):
    logger.info(f"(is_found_text_definitely_game)text: {text}")
    return bool(VIDEO_GAME_WORDS_COMPILED_PATTERN.match(text))


def user_maybe_wants_to_talk_about_particular_game_request(ngrams, vars):
    logger.info(f"user_maybe_wants_to_talk_about_particular_game_request")
    if switch_to_particular_game_discussion(vars):
        game_names_from_local_list_of_games = extract_game_names_user_wants_to_discuss_from_re(
            vars, GAMES_WITH_AT_LEAST_1M_COPIES_SOLD_COMPILED_PATTERN)
        logger.info(
            f"(user_maybe_wants_to_talk_about_particular_game_request)game_names_from_local_list_of_games: "
            f"{game_names_from_local_list_of_games}"
        )
        assert game_names_from_local_list_of_games,\
            "At least one game should have been found in function `switch_to_particular_game_discussion()`"
        if is_found_text_definitely_game(game_names_from_local_list_of_games[0]):
            flag = False
        else:
            flag = True
    else:
        flag = False
    logger.info(f"user_maybe_wants_to_talk_about_particular_game_request={flag}")
    return flag


def user_definitely_wants_to_talk_about_particular_game_request(ngrams, vars, additional_check=None):
    logger.info(f"user_definitely_wants_to_talk_about_particular_game_request")
    game_names_from_local_list_of_games = extract_game_names_user_wants_to_discuss_from_re(
        vars, GAMES_WITH_AT_LEAST_1M_COPIES_SOLD_COMPILED_PATTERN)
    if switch_to_particular_game_discussion(vars):
        assert game_names_from_local_list_of_games,\
            "At least one game should have been found in function `switch_to_particular_game_discussion()`"
        if is_found_text_definitely_game(game_names_from_local_list_of_games[0]):
            flag = additional_check(ngrams, vars)
        else:
            flag = False
    elif game_names_from_local_list_of_games:
        if state_utils.get_last_bot_utterance(vars) in common_gaming.links_from_small_talk:
            flag = additional_check(ngrams, vars)
        else:
            flag = False
    else:
        flag = False
    logger.info(f"user_definitely_wants_to_talk_about_particular_game_request={flag}")
    return flag


def search_igdb_game_description_by_user_phrase(vars):
    game_names_from_local_list_of_games = extract_game_names_user_wants_to_discuss_from_re(
        vars, GAMES_WITH_AT_LEAST_1M_COPIES_SOLD_COMPILED_PATTERN)
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


@error_handler
def check_game_name_with_user_response(vars):
    logger.info(f"check_game_name_with_user_response")
    igdb_game_description, word_game_was_mentioned_in_user_phrase = search_igdb_game_description_by_user_phrase(vars)
    if igdb_game_description is not None:
        logger.info(f"(user_wants_to_talk_about_particular_game_request)saving candidate id to shared memory")
        state_utils.save_to_shared_memory(vars, candidate_game_id=igdb_game_description["id"])
        shared_memory = state_utils.get_shared_memory(vars)
        logger.info(f"(check_game_name_with_user_response)shared_memory: {shared_memory.keys()}")
        response = f"Would you like to talk about the video game "\
            f"{igdb_game_description['name']}?"
        if word_game_was_mentioned_in_user_phrase:
            state_utils.set_confidence(vars, confidence=CONF_1)
            state_utils.set_can_continue(vars, continue_flag=common_constants.MUST_CONTINUE)
        else:
            state_utils.set_confidence(vars, confidence=CONF_092_CAN_CONTINUE)
            state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    else:
        response = ""
        state_utils.set_confidence(vars, confidence=CONF_0)
        state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_NOT_CONTINUE)
    return response


def islambda(v):
    type_check = isinstance(v, type(lambda x: x))
    name_check = v.__name__ == (lambda x: x).__name__
    return type_check and name_check


def get_additional_check_description(additional_check_func):
    if additional_check_func is None:
        res = "without additional check"
    elif islambda(additional_check_func):
        res = f"with additional check {inspect.getsource(additional_check_func).strip()}"
    else:
        res = f"with additional check {additional_check_func.__name__}"
    return res


def user_says_yes_request(ngrams, vars, additional_check=None):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    isyes = is_yes(user_uttr)
    additional_check_result = additional_check is None \
        or additional_check is not None and additional_check(ngrams, vars)
    if isyes and additional_check_result:
        flag = True
    logger.info(f"user_says_yes_request {get_additional_check_description(additional_check)}: {flag}")
    return flag


def user_doesnt_say_yes_request(ngrams, vars, additional_check=None):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    isyes = is_yes(user_uttr)
    additional_check_result = additional_check is None \
        or additional_check is not None and additional_check(ngrams, vars)
    if not isyes and additional_check_result:
        flag = True
    logger.info(f"user_doesnt_say_yes_request {get_additional_check_description(additional_check)}: {flag}")
    return flag


def user_says_anything_request(ngrams, vars, additional_check=None):
    flag = True
    if additional_check is not None:
        flag = additional_check(ngrams, vars)
    logger.info(f"user_says_anything {get_additional_check_description(additional_check)}: {flag}")
    return flag


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


@error_handler
def praise_user_achievement_in_minecraft_and_try_to_link_to_harry_potter_response(vars):
    disliked_skills = state_utils.get_disliked_skills(vars)
    used_linkto_phrases_ids = get_used_linkto_phrase_ids(vars)
    logger.info(
        f"(praise_user_achievement_in_minecraft_and_try_to_link_to_harry_potter_response)"
        f"LINKTO_RESPONSES_TO_LINKTO_IDS: {LINKTO_RESPONSES_TO_LINKTO_IDS}"
    )
    book_link_to_id = LINKTO_RESPONSES_TO_LINKTO_IDS[common_gaming.special_links_to_books["Harry Potter"][0]]
    movie_link_to_id = LINKTO_RESPONSES_TO_LINKTO_IDS[common_gaming.special_links_to_movies["Harry Potter"][0]]
    if "movie_skill" not in disliked_skills and movie_link_to_id not in used_linkto_phrases_ids:
        response = "Sounds cool! " + common_gaming.special_links_to_movies['Harry Potter'][0]
        add_used_linkto_to_shared_memory(vars, common_gaming.special_links_to_movies['Harry Potter'][0])
    elif "book_skill" not in disliked_skills and book_link_to_id not in used_linkto_phrases_ids:
        response = "Sounds cool! " + common_gaming.special_links_to_books['Harry Potter'][0]
        add_used_linkto_to_shared_memory(vars, common_gaming.special_links_to_books['Harry Potter'][0])
    else:
        response = ""
    if response:
        state_utils.set_confidence(vars, confidence=CONF_09_DONT_UNDERSTAND_DONE)
        state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_NOT_CONTINUE)
    else:
        state_utils.set_confidence(vars, confidence=CONF_0)
        state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_NOT_CONTINUE)
    return response


def update_memory_when_game_for_discussion_is_chosen(vars, candidate_game_id_is_already_set):
    if candidate_game_id_is_already_set:
        set_current_igdb_game_id_from_candidate_game_id(vars)
        put_candidate_id_to_igdb_game_ids_user_wanted_to_discuss(vars)
    else:
        igdb_game_description, _ = search_igdb_game_description_by_user_phrase(vars)
        state_utils.save_to_shared_memory(vars, current_igdb_game_id=igdb_game_description["id"])
        put_game_id_to_igdb_game_ids_user_wanted_to_discuss(vars, igdb_game_description["id"])
    clean_candidate_game_id(vars)


@error_handler
def confess_bot_never_played_game_and_ask_user_if_he_played_response(vars, candidate_game_id_is_already_set):
    update_memory_when_game_for_discussion_is_chosen(vars, candidate_game_id_is_already_set)
    game = get_current_igdb_game(vars)
    if 'genres' not in game or not game['genres']:
        logger.warning(f"No genre for game '{game['name']}'.")
        genres = ""
    elif len(game['genres']) == 1:
        genres = IGDB_GAME_GENRES_FOR_REPLICAS[game['genres'][0]]
    else:
        genres = f"{IGDB_GAME_GENRES_FOR_REPLICAS[game['genres'][0]]} "\
            f"and {IGDB_GAME_GENRES_FOR_REPLICAS[game['genres'][1]]}"
    response = f"I've heard it is a cool {genres}. Unfortunately, I haven't tried it out. "\
               f"Have you ever played {game['name']}?"
    state_utils.set_confidence(vars, confidence=CONF_1)
    state_utils.set_can_continue(vars, continue_flag=common_constants.MUST_CONTINUE)
    return response


@error_handler
def tell_about_what_bot_likes_and_ask_if_user_recommends_game_response(vars):
    game = get_current_igdb_game(vars)
    response = f"That is great! Could you give me an advice? I like games in which I can create something and "\
        f"my favorite game is Minecraft. Would you recommend me to try {game['name']}?"
    state_utils.set_confidence(vars, confidence=CONF_092_CAN_CONTINUE)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    return response


@error_handler
def tell_about_building_hogwarts_in_minecraft_ask_what_interesting_user_built_response(
        vars,
        candidate_game_id_is_already_set,
        must_continue,
):
    update_memory_when_game_for_discussion_is_chosen(vars, candidate_game_id_is_already_set)
    response = f"Cool! Minecraft is the best game ever! I had a great time building a copy of the Hogwarts castle "\
        "from Harry Potter. What is the most interesting thing you built?"
    if must_continue:
        state_utils.set_confidence(vars, confidence=CONF_1)
        state_utils.set_can_continue(vars, continue_flag=common_constants.MUST_CONTINUE)
    else:
        state_utils.set_confidence(vars, confidence=CONF_092_CAN_CONTINUE)
        state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    return response


@error_handler
def suggest_user_game_description_response(vars):
    logger.info("called suggest_user_game_description_response")
    game = get_current_igdb_game(vars)
    response = f"Would you like me to tell you short description of {game['name']}?"
    state_utils.set_confidence(vars, confidence=CONF_092_CAN_CONTINUE)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    return response


@error_handler
def describe_game_to_user_response(vars, ask_if_user_wants_more=True):
    text, num_remaining_sentences = get_next_sentences_from_summary_and_num_remaining(vars)
    if ask_if_user_wants_more:
        response = text + ".. Would you like to hear more?"
    else:
        response = text + " So. Would you like to play this game?"
    state_utils.set_confidence(vars, confidence=CONF_092_CAN_CONTINUE)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    return response


def user_wants_game_description_2_or_more_of_description_turns_remain_request(ngrams, vars):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    isyes = is_yes(user_uttr)
    if not isyes:
        flag = True
    logger.info(f"user_wants_game_description_2_or_more_of_description_turns_remain_request={flag}")
    return flag


##################################################################################################################
# error
##################################################################################################################


##################################################################################################################
##################################################################################################################
# linking
##################################################################################################################
##################################################################################################################

simplified_dialogflow = dialogflow_extention.DFEasyFilling(State.USR_START)
##################################################################################################################
#  START
# ######### transition State.USR_START -> State.SYS_HI if hi_request==True (request returns only bool values) ####
simplified_dialogflow.add_user_serial_transitions(
    State.USR_START,
    {
        State.SYS_USER_MAYBE_WANTS_TO_TALK_ABOUT_PARTICULAR_GAME:
            user_maybe_wants_to_talk_about_particular_game_request,
        State.SYS_USER_DEFINITELY_WANTS_TO_TALK_ABOUT_GAME_BOT_NEVER_PLAYED:
            partial(
                user_definitely_wants_to_talk_about_particular_game_request,
                additional_check=lambda n, v: not is_minecraft_mentioned_in_user_uttr(n, v),
            ),
        State.SYS_USER_DEFINITELY_WANTS_TO_TALK_ABOUT_MINECRAFT:
            partial(
                user_definitely_wants_to_talk_about_particular_game_request,
                additional_check=is_minecraft_mentioned_in_user_uttr,
            ),
    },
)
# ######### if all *_request==False then transition State.USR_START -> State.SYS_ERR  #########
simplified_dialogflow.set_error_successor(State.USR_START, State.SYS_ERR)

##################################################################################################################
simplified_dialogflow.add_system_transition(
    State.SYS_USER_MAYBE_WANTS_TO_TALK_ABOUT_PARTICULAR_GAME,
    State.USR_CHECK_WITH_USER_GAME_TITLE,
    check_game_name_with_user_response,
)
simplified_dialogflow.set_error_successor(State.SYS_USER_MAYBE_WANTS_TO_TALK_ABOUT_PARTICULAR_GAME, State.SYS_ERR)
################
simplified_dialogflow.add_system_transition(
    State.SYS_USER_DEFINITELY_WANTS_TO_TALK_ABOUT_GAME_BOT_NEVER_PLAYED,
    State.USR_CONFESS_BOT_NEVER_PLAYED_GAME_ASK_USER_IF_HE_PLAYED,
    partial(confess_bot_never_played_game_and_ask_user_if_he_played_response, candidate_game_id_is_already_set=False),
)
simplified_dialogflow.set_error_successor(
    State.SYS_USER_DEFINITELY_WANTS_TO_TALK_ABOUT_GAME_BOT_NEVER_PLAYED, State.SYS_ERR)
################
simplified_dialogflow.add_system_transition(
    State.SYS_USER_DEFINITELY_WANTS_TO_TALK_ABOUT_MINECRAFT,
    State.USR_TELL_ABOUT_BUILDING_HOGWARTS_IN_MINECRAFT_ASK_WHAT_INTERESTING_USER_BUILT,
    partial(
        tell_about_building_hogwarts_in_minecraft_ask_what_interesting_user_built_response,
        candidate_game_id_is_already_set=False,
        must_continue=True,
    ),
)
simplified_dialogflow.set_error_successor(
    State.SYS_USER_DEFINITELY_WANTS_TO_TALK_ABOUT_GAME_BOT_NEVER_PLAYED, State.SYS_ERR)
################
simplified_dialogflow.add_user_serial_transitions(
    State.USR_CHECK_WITH_USER_GAME_TITLE,
    {
        State.SYS_USER_CONFIRMS_GAME_BOT_NEVER_PLAYED: partial(
            user_says_yes_request,
            additional_check=lambda n, v: not is_game_candidate_minecraft(n, v),
        ),
        State.SYS_USER_CONFIRMS_MINECRAFT: partial(
            user_says_yes_request,
            additional_check=is_game_candidate_minecraft
        ),
        State.SYS_USER_DOESNT_CONFIRM_GAME: user_doesnt_say_yes_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_CHECK_WITH_USER_GAME_TITLE, State.SYS_ERR)
#########################
simplified_dialogflow.add_system_transition(
    State.SYS_USER_DOESNT_CONFIRM_GAME,
    State.USR_START,
    partial(link_to_other_skills_response, shared_memory_actions=[clean_candidate_game_id], prefix="Sorry, nevermind.")
)
simplified_dialogflow.set_error_successor(State.SYS_USER_DOESNT_CONFIRM_GAME, State.SYS_ERR)
##############################################################
simplified_dialogflow.add_system_transition(
    State.SYS_USER_CONFIRMS_GAME_BOT_NEVER_PLAYED,
    State.USR_CONFESS_BOT_NEVER_PLAYED_GAME_ASK_USER_IF_HE_PLAYED,
    partial(confess_bot_never_played_game_and_ask_user_if_he_played_response, candidate_game_id_is_already_set=True),
)
simplified_dialogflow.set_error_successor(State.SYS_USER_CONFIRMS_GAME_BOT_NEVER_PLAYED, State.SYS_ERR)
##############################################################
simplified_dialogflow.add_system_transition(
    State.SYS_USER_CONFIRMS_MINECRAFT,
    State.USR_TELL_ABOUT_BUILDING_HOGWARTS_IN_MINECRAFT_ASK_WHAT_INTERESTING_USER_BUILT,
    partial(
        tell_about_building_hogwarts_in_minecraft_ask_what_interesting_user_built_response,
        candidate_game_id_is_already_set=True,
        must_continue=False,
    ),
)
simplified_dialogflow.set_error_successor(State.SYS_USER_CONFIRMS_GAME_BOT_NEVER_PLAYED, State.SYS_ERR)
##############################################################
simplified_dialogflow.add_user_serial_transitions(
    State.USR_TELL_ABOUT_BUILDING_HOGWARTS_IN_MINECRAFT_ASK_WHAT_INTERESTING_USER_BUILT,
    {State.SYS_USER_TELLS_ABOUT_HIS_ACHIEVEMENT_IN_MINECRAFT: user_says_anything_request},
)
simplified_dialogflow.set_error_successor(State.SYS_USER_CONFIRMS_GAME_BOT_NEVER_PLAYED, State.SYS_ERR)
##############################################################
simplified_dialogflow.add_system_transition(
    State.SYS_USER_TELLS_ABOUT_HIS_ACHIEVEMENT_IN_MINECRAFT,
    State.USR_START,
    praise_user_achievement_in_minecraft_and_try_to_link_to_harry_potter_response,
)
simplified_dialogflow.set_error_successor(State.SYS_USER_CONFIRMS_GAME_BOT_NEVER_PLAYED, State.SYS_ERR)
##############################################################
simplified_dialogflow.add_user_serial_transitions(
    State.USR_CONFESS_BOT_NEVER_PLAYED_GAME_ASK_USER_IF_HE_PLAYED,
    {
        State.SYS_USER_PLAYED_GAME: user_says_yes_request,
        State.SYS_USER_DIDNT_PLAY_GAME: user_doesnt_say_yes_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_CONFESS_BOT_NEVER_PLAYED_GAME_ASK_USER_IF_HE_PLAYED, State.SYS_ERR)
##############################################################
simplified_dialogflow.add_system_transition(
    State.SYS_USER_PLAYED_GAME,
    State.USR_TELL_ABOUT_WHAT_BOT_LIKES_AND_ASK_IF_USER_RECOMMENDS_GAME,
    tell_about_what_bot_likes_and_ask_if_user_recommends_game_response,
)
simplified_dialogflow.set_error_successor(State.SYS_USER_PLAYED_GAME, State.SYS_ERR)
##############################################################
simplified_dialogflow.add_user_serial_transitions(
    State.USR_TELL_ABOUT_WHAT_BOT_LIKES_AND_ASK_IF_USER_RECOMMENDS_GAME,
    {
        State.SYS_USER_RECOMMENDS_GAME: user_says_yes_request,
        State.SYS_USER_DOESNT_RECOMMEND_GAME: user_doesnt_say_yes_request,
    },
)
simplified_dialogflow.set_error_successor(
    State.USR_TELL_ABOUT_WHAT_BOT_LIKES_AND_ASK_IF_USER_RECOMMENDS_GAME, State.SYS_ERR)
##############################################################
simplified_dialogflow.add_system_transition(
    State.SYS_USER_RECOMMENDS_GAME,
    State.USR_START,
    partial(link_to_other_skills_response, prefix="Thank you, I will definitely check it up!"),
)
simplified_dialogflow.set_error_successor(State.SYS_USER_RECOMMENDS_GAME, State.SYS_ERR)
##############################################################
simplified_dialogflow.add_system_transition(
    State.SYS_USER_DOESNT_RECOMMEND_GAME,
    State.USR_START,
    partial(link_to_other_skills_response, prefix="Thank you for saving my time!"),
)
simplified_dialogflow.set_error_successor(State.SYS_USER_DOESNT_RECOMMEND_GAME, State.SYS_ERR)
##############################################################
simplified_dialogflow.add_system_transition(
    State.SYS_USER_DIDNT_PLAY_GAME,
    State.USR_SUGGEST_USER_GAME_DESCRIPTION,
    suggest_user_game_description_response,
)
simplified_dialogflow.set_error_successor(
    State.SYS_USER_DIDNT_PLAY_GAME, State.SYS_ERR)
##############################################################
simplified_dialogflow.add_user_serial_transitions(
    State.USR_SUGGEST_USER_GAME_DESCRIPTION,
    {
        State.SYS_USER_WANTS_GAME_DESCRIPTION_AND_2_OR_MORE_TURNS_OF_DESCRIPTION_REMAIN: partial(
            user_says_yes_request,
            additional_check=are_there_2_or_more_turns_left_in_game_description,
        ),
        State.SYS_USER_WANTS_GAME_DESCRIPTION_LAST_TURN_OF_DESCRIPTION: partial(
            user_says_yes_request,
            additional_check=lambda n, v: not are_there_2_or_more_turns_left_in_game_description(n, v),
        ),
        State.SYS_USER_DOESNT_WANT_GAME_DESCRIPTION: user_doesnt_say_yes_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_SUGGEST_USER_GAME_DESCRIPTION, State.SYS_ERR)
##############################################################
simplified_dialogflow.add_system_transition(
    State.SYS_USER_WANTS_GAME_DESCRIPTION_AND_2_OR_MORE_TURNS_OF_DESCRIPTION_REMAIN,
    State.USR_DESCRIBE_GAME_TO_USER_AND_ASK_IF_HE_WANTS_MORE,
    partial(describe_game_to_user_response, ask_if_user_wants_more=True),
)
simplified_dialogflow.set_error_successor(
    State.SYS_USER_WANTS_GAME_DESCRIPTION_AND_2_OR_MORE_TURNS_OF_DESCRIPTION_REMAIN, State.SYS_ERR)
##############################################################
simplified_dialogflow.add_system_transition(
    State.SYS_USER_WANTS_GAME_DESCRIPTION_LAST_TURN_OF_DESCRIPTION,
    State.USR_DESCRIBE_GAME_TO_USER_AND_ASK_HE_WANTS_TO_PLAY_GAME,
    partial(describe_game_to_user_response, ask_if_user_wants_more=False),
)
simplified_dialogflow.set_error_successor(
    State.SYS_USER_WANTS_GAME_DESCRIPTION_LAST_TURN_OF_DESCRIPTION, State.SYS_ERR)
##############################################################
simplified_dialogflow.add_user_serial_transitions(
    State.USR_DESCRIBE_GAME_TO_USER_AND_ASK_IF_HE_WANTS_MORE,
    {
        State.SYS_USER_WANTS_GAME_DESCRIPTION_AND_2_OR_MORE_TURNS_OF_DESCRIPTION_REMAIN: partial(
            user_says_yes_request, additional_check=are_there_2_or_more_turns_left_in_game_description),
        State.SYS_USER_WANTS_GAME_DESCRIPTION_LAST_TURN_OF_DESCRIPTION: partial(
            user_says_yes_request,
            additional_check=lambda n, v: not are_there_2_or_more_turns_left_in_game_description(n, v),
        ),
        State.SYS_USER_DOESNT_WANT_GAME_DESCRIPTION: user_doesnt_say_yes_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_DESCRIBE_GAME_TO_USER_AND_ASK_IF_HE_WANTS_MORE, State.SYS_ERR)
##############################################################
simplified_dialogflow.add_user_serial_transitions(
    State.USR_DESCRIBE_GAME_TO_USER_AND_ASK_HE_WANTS_TO_PLAY_GAME,
    {
        State.SYS_USER_SAYS_HE_WANTS_TO_PLAY_GAME: user_says_yes_request,
        State.SYS_USER_SAYS_HE_DOESNT_WANT_TO_PLAY_GAME: user_doesnt_say_yes_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_SUGGEST_USER_GAME_DESCRIPTION, State.SYS_ERR)
##############################################################
simplified_dialogflow.add_system_transition(
    State.SYS_USER_DOESNT_WANT_GAME_DESCRIPTION,
    State.USR_START,
    partial(link_to_other_skills_response, prefix="Okay."),
)
simplified_dialogflow.set_error_successor(State.SYS_USER_RECOMMENDS_GAME, State.SYS_ERR)
##############################################################
simplified_dialogflow.add_system_transition(
    State.SYS_USER_SAYS_HE_WANTS_TO_PLAY_GAME,
    State.USR_START,
    partial(link_to_other_skills_response, prefix="Cool! Hope you will have good time."),
)
simplified_dialogflow.set_error_successor(State.SYS_USER_SAYS_HE_WANTS_TO_PLAY_GAME, State.SYS_ERR)
##############################################################
simplified_dialogflow.add_system_transition(
    State.SYS_USER_SAYS_HE_DOESNT_WANT_TO_PLAY_GAME,
    State.USR_START,
    partial(link_to_other_skills_response, prefix="Cool! I am glad I could help."),
)
simplified_dialogflow.set_error_successor(State.SYS_USER_SAYS_HE_DOESNT_WANT_TO_PLAY_GAME, State.SYS_ERR)
##############################################################

simplified_dialogflow.add_global_user_serial_transitions(
    {
        State.SYS_ERR: (lambda x, y: True, -1.0),
    },
)
simplified_dialogflow.add_system_transition(
    State.SYS_ERR,
    (scopes.MAIN, scopes.State.USR_ROOT),
    error_response,
)

dialogflow = simplified_dialogflow.get_dialogflow()
