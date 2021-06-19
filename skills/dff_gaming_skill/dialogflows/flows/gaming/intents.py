import logging
import os

import sentry_sdk

import common.dialogflow_framework.utils.state as state_utils
from common.gaming import GAMES_WITH_AT_LEAST_1M_COPIES_SOLD_COMPILED_PATTERN, skill_trigger_phrases
from common.link import link_to_skill2i_like_to_talk
from common.utils import is_yes

import dialogflows.common.intents as common_intents
from dialogflows.common.game_info import does_text_contain_video_game_words


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))

logger = logging.getLogger(__name__)


WORDS_THAT_ARE_DEFINITELY_GAME_NAMES = ["minecraft"]


def get_links_to_gaming():
    return skill_trigger_phrases() + link_to_skill2i_like_to_talk['dff_gaming_skill']


def does_text_contain_link_to_gaming(text):
    link_phrases = get_links_to_gaming()
    logger.info(f"(does_text_contain_link_to_gaming)text: {text}")
    logger.info(f"(does_text_contain_link_to_gaming)link_phrases: {link_phrases}")
    res = any([u.lower() in text.lower() for u in link_phrases])
    logger.info(f"(does_text_contain_link_to_gaming)res: {res}")
    return res


def user_maybe_wants_to_talk_about_particular_game_request(ngrams, vars):
    logger.info(f"user_maybe_wants_to_talk_about_particular_game_request")
    user_text = state_utils.get_last_human_utterance(vars).get("text", "").lower()
    bot_text = state_utils.get_last_bot_utterance(vars).get("text", "").lower()
    game_names_from_local_list_of_games = GAMES_WITH_AT_LEAST_1M_COPIES_SOLD_COMPILED_PATTERN.findall(user_text) \
        + GAMES_WITH_AT_LEAST_1M_COPIES_SOLD_COMPILED_PATTERN.findall(bot_text)
    if game_names_from_local_list_of_games:
        if does_text_contain_link_to_gaming(bot_text):
            logger.info("performing additional check")
            flag = False
        elif common_intents.switch_to_particular_game_discussion(vars):
            assert game_names_from_local_list_of_games,\
                "At least one game should have been found in function `switch_to_particular_game_discussion()`"
            possible_game_name = game_names_from_local_list_of_games[0]
            flag = not any([n.lower() in possible_game_name.lower() for n in WORDS_THAT_ARE_DEFINITELY_GAME_NAMES]) \
                and not does_text_contain_video_game_words(user_text) \
                and not does_text_contain_link_to_gaming(bot_text)
        else:
            flag = False
    else:
        flag = False
    logger.info(f"user_maybe_wants_to_talk_about_particular_game_request={flag}")
    return flag


def user_definitely_wants_to_talk_about_particular_game_request(ngrams, vars, additional_check=None):
    logger.info(f"user_definitely_wants_to_talk_about_particular_game_request")
    user_text = state_utils.get_last_human_utterance(vars).get("text", "").lower()
    bot_text = state_utils.get_last_bot_utterance(vars).get("text", "").lower()
    game_names_from_local_list_of_games = GAMES_WITH_AT_LEAST_1M_COPIES_SOLD_COMPILED_PATTERN.findall(user_text) \
        + GAMES_WITH_AT_LEAST_1M_COPIES_SOLD_COMPILED_PATTERN.findall(bot_text)
    if game_names_from_local_list_of_games:
        if does_text_contain_link_to_gaming(bot_text):
            logger.info("performing additional check")
            flag = additional_check(ngrams, vars)
        elif common_intents.switch_to_particular_game_discussion(vars):
            assert game_names_from_local_list_of_games,\
                "At least one game should have been found in function `switch_to_particular_game_discussion()`"
            possible_game_name = game_names_from_local_list_of_games[0]
            flag = (
                any([n.lower() in possible_game_name.lower() for n in WORDS_THAT_ARE_DEFINITELY_GAME_NAMES])
                or does_text_contain_video_game_words(user_text)
                or does_text_contain_video_game_words(bot_text)
            ) and additional_check(ngrams, vars)
        else:
            flag = False
    else:
        flag = False
    logger.info(f"user_definitely_wants_to_talk_about_particular_game_request with additional check "
                f"{common_intents.get_additional_check_description(additional_check)}: {flag}")
    return flag


def user_wants_game_description_2_or_more_of_description_turns_remain_request(ngrams, vars):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    isyes = is_yes(user_uttr)
    if not isyes:
        flag = True
    logger.info(f"user_wants_game_description_2_or_more_of_description_turns_remain_request={flag}")
    return flag
