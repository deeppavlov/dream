import logging
import os

import sentry_sdk

import common.dialogflow_framework.utils.state as state_utils
from common.gaming import ANSWER_TO_GENERAL_WISH_TO_DISCUSS_VIDEO_GAMES_AND_QUESTION_WHAT_GAME_YOU_PLAY, \
    GAMES_WITH_AT_LEAST_1M_COPIES_SOLD_COMPILED_PATTERN, skill_trigger_phrases
from common.link import link_to_skill2i_like_to_talk
from common.utils import is_no, is_yes

import dialogflows.common.intents as common_intents
from dialogflows.flows.minecraft.intents import is_minecraft_mentioned_in_user_uttr
from dialogflows.common.game_info import does_text_contain_video_game_words


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))

logger = logging.getLogger(__name__)


WORDS_THAT_ARE_DEFINITELY_GAME_NAMES = ["minecraft"]


def get_links_to_gaming():
    return skill_trigger_phrases() \
        + link_to_skill2i_like_to_talk['dff_gaming_skill'] \
        + [ANSWER_TO_GENERAL_WISH_TO_DISCUSS_VIDEO_GAMES_AND_QUESTION_WHAT_GAME_YOU_PLAY]


def does_text_contain_link_to_gaming(text):
    link_phrases = get_links_to_gaming()
    logger.info(f"(does_text_contain_link_to_gaming)text: {text}")
    logger.info(f"(does_text_contain_link_to_gaming)link_phrases: {link_phrases}")
    res = any([u.lower() in text.lower() for u in link_phrases])
    logger.info(f"(does_text_contain_link_to_gaming)res: {res}")
    return res


def user_mentioned_games_as_his_interest_request(ngrams, vars, first_time=True):
    logger.info(f"user_mentioned_games_as_his_interest_request")
    user_text = state_utils.get_last_human_utterance(vars).get("text", "").lower()
    bot_text = state_utils.get_last_bot_utterance(vars).get("text", "").lower()
    game_names_from_local_list_of_games = GAMES_WITH_AT_LEAST_1M_COPIES_SOLD_COMPILED_PATTERN.findall(user_text) \
        + GAMES_WITH_AT_LEAST_1M_COPIES_SOLD_COMPILED_PATTERN.findall(bot_text)
    flag = not game_names_from_local_list_of_games \
        and common_intents.switch_to_general_gaming_discussion(vars) \
        and not user_doesnt_like_gaming_request(ngrams, vars) \
        and not user_didnt_name_game_request(ngrams, vars) \
        and (
            first_time
            and ANSWER_TO_GENERAL_WISH_TO_DISCUSS_VIDEO_GAMES_AND_QUESTION_WHAT_GAME_YOU_PLAY not in bot_text
            or not first_time
            and ANSWER_TO_GENERAL_WISH_TO_DISCUSS_VIDEO_GAMES_AND_QUESTION_WHAT_GAME_YOU_PLAY in bot_text
        )
    logger.info(f"user_mentioned_games_as_his_interest_request={flag}")
    return flag


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
        if common_intents.switch_to_particular_game_discussion(vars) \
                and not does_text_contain_link_to_gaming(bot_text):
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


def user_definitely_wants_to_talk_about_game_that_user_played_and_bot_didnt_play_request(
        ngrams, vars, additional_check=None):
    logger.info(f"user_definitely_wants_to_talk_about_game_that_user_played_and_bot_didnt_play")
    user_uttr = state_utils.get_last_human_utterance(vars)
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    game_names_from_local_list_of_games = GAMES_WITH_AT_LEAST_1M_COPIES_SOLD_COMPILED_PATTERN.findall(
        user_uttr.get("text", ""))
    flag = bool(game_names_from_local_list_of_games) \
        and does_text_contain_link_to_gaming(bot_uttr.get("text", "")) \
        and additional_check(ngrams, vars)
    logger.info(f"user_definitely_wants_to_talk_about_game_that_user_played_and_bot_didnt_play with additional check "
                f"{common_intents.get_additional_check_description(additional_check)}: {flag}")
    return flag


def user_doesnt_like_gaming_request(ngrams, vars):
    logger.info(f"user_doesnt_like_gaming_request")
    user_uttr = state_utils.get_last_human_utterance(vars)
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    found_game_name = bool(GAMES_WITH_AT_LEAST_1M_COPIES_SOLD_COMPILED_PATTERN.findall(user_uttr.get("text", "")))
    flag = is_no(user_uttr) and not found_game_name and does_text_contain_link_to_gaming(bot_uttr.get("text", ""))
    logger.info(f"user_doesnt_like_gaming_request={flag}")
    return flag


def user_didnt_name_game_request(ngrams, vars):
    logger.info(f"user_didnt_name_game_request")
    user_uttr = state_utils.get_last_human_utterance(vars)
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    found_game_name = bool(GAMES_WITH_AT_LEAST_1M_COPIES_SOLD_COMPILED_PATTERN.findall(user_uttr.get("text", "")))
    flag = not is_no(user_uttr) and not found_game_name and does_text_contain_link_to_gaming(bot_uttr.get("text", ""))
    logger.info(f"user_didnt_name_game_request={flag}")
    return flag


def user_wants_to_discuss_minecraft_request(ngrams, vars):
    return user_definitely_wants_to_talk_about_particular_game_request(
        ngrams,
        vars,
        additional_check=is_minecraft_mentioned_in_user_uttr,
    ) or user_definitely_wants_to_talk_about_game_that_user_played_and_bot_didnt_play_request(
        ngrams, vars, additional_check=is_minecraft_mentioned_in_user_uttr)


def user_wants_game_description_2_or_more_of_description_turns_remain_request(ngrams, vars):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    isyes = is_yes(user_uttr)
    if not isyes:
        flag = True
    logger.info(f"user_wants_game_description_2_or_more_of_description_turns_remain_request={flag}")
    return flag
