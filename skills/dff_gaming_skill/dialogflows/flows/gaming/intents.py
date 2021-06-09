import logging
import os

import sentry_sdk

import common.dialogflow_framework.utils.state as state_utils
import common.gaming as common_gaming
from common.gaming import GAMES_WITH_AT_LEAST_1M_COPIES_SOLD_COMPILED_PATTERN, VIDEO_GAME_WORDS_COMPILED_PATTERN
from common.utils import is_yes

import dialogflows.common.intents as common_intents


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))

logger = logging.getLogger(__name__)


WORDS_THAT_ARE_DEFINITELY_GAME_NAMES = ["minecraft"]


def does_text_contain_video_game_words(text):
    logger.info(f"(is_found_text_definitely_game)text: {text}")
    return bool(VIDEO_GAME_WORDS_COMPILED_PATTERN.match(text))


def user_maybe_wants_to_talk_about_particular_game_request(ngrams, vars):
    logger.info(f"user_maybe_wants_to_talk_about_particular_game_request")
    if common_intents.switch_to_particular_game_discussion(vars):
        user_uttr = state_utils.get_last_human_utterance(vars)
        game_names_from_local_list_of_games = GAMES_WITH_AT_LEAST_1M_COPIES_SOLD_COMPILED_PATTERN.findall(
            user_uttr.get("text", ""))
        logger.info(
            f"(user_maybe_wants_to_talk_about_particular_game_request)game_names_from_local_list_of_games: "
            f"{game_names_from_local_list_of_games}"
        )
        assert game_names_from_local_list_of_games,\
            "At least one game should have been found in function `switch_to_particular_game_discussion()`"
        possible_game_name = game_names_from_local_list_of_games[0]
        if does_text_contain_video_game_words(possible_game_name) \
                or any([possible_game_name.lower() in n.lower() for n in WORDS_THAT_ARE_DEFINITELY_GAME_NAMES]):
            flag = False
        else:
            flag = True
    else:
        flag = False
    logger.info(f"user_maybe_wants_to_talk_about_particular_game_request={flag}")
    return flag


def user_definitely_wants_to_talk_about_particular_game_request(ngrams, vars, additional_check=None):
    logger.info(f"user_definitely_wants_to_talk_about_particular_game_request")
    user_uttr = state_utils.get_last_human_utterance(vars)
    game_names_from_local_list_of_games = GAMES_WITH_AT_LEAST_1M_COPIES_SOLD_COMPILED_PATTERN.findall(
        user_uttr.get("text", ""))
    if common_intents.switch_to_particular_game_discussion(vars):
        assert game_names_from_local_list_of_games,\
            "At least one game should have been found in function `switch_to_particular_game_discussion()`"
        possible_game_name = game_names_from_local_list_of_games[0]
        if does_text_contain_video_game_words(possible_game_name) \
                or any([possible_game_name.lower() in n.lower() for n in WORDS_THAT_ARE_DEFINITELY_GAME_NAMES]):
            flag = additional_check(ngrams, vars)
        else:
            flag = False
    elif game_names_from_local_list_of_games:
        if state_utils.get_last_bot_utterance(vars).get("text", "") in common_gaming.links_from_small_talk:
            flag = additional_check(ngrams, vars)
        else:
            flag = False
    else:
        flag = False
    logger.info(f"user_definitely_wants_to_talk_about_particular_game_request={flag}")
    return flag


def user_wants_game_description_2_or_more_of_description_turns_remain_request(ngrams, vars):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    isyes = is_yes(user_uttr)
    if not isyes:
        flag = True
    logger.info(f"user_wants_game_description_2_or_more_of_description_turns_remain_request={flag}")
    return flag
