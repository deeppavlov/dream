import logging
import os

import sentry_sdk

import common.dialogflow_framework.utils.state as state_utils
from common.gaming import ANSWER_TO_GENERAL_WISH_TO_DISCUSS_VIDEO_GAMES_AND_QUESTION_WHAT_GAME_YOU_PLAY, \
    GAMES_WITH_AT_LEAST_1M_COPIES_SOLD_COMPILED_PATTERN, VIDEO_GAME_WORDS_COMPILED_PATTERN, find_games_in_text, \
    skill_trigger_phrases

from common.link import link_to_skill2i_like_to_talk
from common.universal_templates import if_chat_about_particular_topic
from common.utils import is_no, is_yes

import dialogflows.common.intents as common_intents
from dialogflows.flows.minecraft.intents import is_minecraft_mentioned_in_user_or_bot_uttr
from dialogflows.common.game_info import does_text_contain_video_game_words
from dialogflows.common.shared_memory_ops import was_link_from_gaming_to_other_skill_made_in_previous_bot_utterance


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
    user_uttr = state_utils.get_last_human_utterance(vars)
    user_text = user_uttr.get("text", "").lower()
    bot_text = state_utils.get_last_bot_utterance(vars).get("text", "").lower()
    game_names_from_local_list_of_games = find_games_in_text(user_text) + find_games_in_text(bot_text)
    flag = not game_names_from_local_list_of_games \
        and common_intents.switch_to_general_gaming_discussion(vars) \
        and not user_doesnt_like_gaming_request(ngrams, vars) \
        and not user_didnt_name_game_after_question_about_games_and_didnt_refuse_to_discuss_request(ngrams, vars) \
        and (
            first_time
            and ANSWER_TO_GENERAL_WISH_TO_DISCUSS_VIDEO_GAMES_AND_QUESTION_WHAT_GAME_YOU_PLAY not in bot_text
            or not first_time
            and ANSWER_TO_GENERAL_WISH_TO_DISCUSS_VIDEO_GAMES_AND_QUESTION_WHAT_GAME_YOU_PLAY in bot_text
        ) and (
            not was_link_from_gaming_to_other_skill_made_in_previous_bot_utterance(vars)
            or was_link_from_gaming_to_other_skill_made_in_previous_bot_utterance(vars)
            and if_chat_about_particular_topic(user_uttr, compiled_pattern=VIDEO_GAME_WORDS_COMPILED_PATTERN)
        )
    logger.info(f"user_mentioned_games_as_his_interest_request={flag}")
    return flag


def user_maybe_wants_to_talk_about_particular_game_request(ngrams, vars):
    user_uttr = state_utils.get_last_human_utterance(vars)
    user_text = user_uttr.get("text", "").lower()
    bot_text = state_utils.get_last_bot_utterance(vars).get("text", "").lower()
    game_names_from_local_list_of_games = find_games_in_text(user_text) + find_games_in_text(bot_text)
    if game_names_from_local_list_of_games:
        if does_text_contain_link_to_gaming(bot_text):
            logger.info("performing additional check")
            flag = False
        elif common_intents.switch_to_particular_game_discussion(vars):
            assert game_names_from_local_list_of_games,\
                "At least one game should have been found in function `switch_to_particular_game_discussion()`"
            possible_game_name = game_names_from_local_list_of_games[0][0]
            flag = not any([n.lower() in possible_game_name.lower() for n in WORDS_THAT_ARE_DEFINITELY_GAME_NAMES]) \
                and not does_text_contain_video_game_words(user_text) \
                and not does_text_contain_link_to_gaming(bot_text) \
                and (
                    not was_link_from_gaming_to_other_skill_made_in_previous_bot_utterance(vars)
                    or was_link_from_gaming_to_other_skill_made_in_previous_bot_utterance(vars)
                    and if_chat_about_particular_topic(
                        user_uttr,
                        compiled_pattern=GAMES_WITH_AT_LEAST_1M_COPIES_SOLD_COMPILED_PATTERN))
        else:
            flag = False
    else:
        flag = False
    logger.info(f"user_maybe_wants_to_talk_about_particular_game_request={flag}")
    return flag


def user_definitely_wants_to_talk_about_particular_game_request(ngrams, vars, additional_check=None):
    user_uttr = state_utils.get_last_human_utterance(vars)
    user_text = user_uttr.get("text", "").lower()
    bot_text = state_utils.get_last_bot_utterance(vars).get("text", "").lower()
    game_names_from_local_list_of_games = find_games_in_text(user_text) + find_games_in_text(bot_text)
    if game_names_from_local_list_of_games:
        if common_intents.switch_to_particular_game_discussion(vars) \
                and not does_text_contain_link_to_gaming(bot_text):
            assert game_names_from_local_list_of_games,\
                "At least one game should have been found in function `switch_to_particular_game_discussion()`"
            possible_game_name = game_names_from_local_list_of_games[0][0]
            flag = (
                any([n.lower() in possible_game_name.lower() for n in WORDS_THAT_ARE_DEFINITELY_GAME_NAMES])
                or does_text_contain_video_game_words(user_text)
                or does_text_contain_video_game_words(bot_text)
            ) \
                and additional_check(ngrams, vars) \
                and (
                    not was_link_from_gaming_to_other_skill_made_in_previous_bot_utterance(vars)
                    or was_link_from_gaming_to_other_skill_made_in_previous_bot_utterance(vars)
                    and if_chat_about_particular_topic(
                        user_uttr,
                        compiled_pattern=GAMES_WITH_AT_LEAST_1M_COPIES_SOLD_COMPILED_PATTERN))
        else:
            flag = False
    else:
        flag = False
    logger.info(f"user_definitely_wants_to_talk_about_particular_game_request "
                f"{common_intents.get_additional_check_description(additional_check)}: {flag}")
    return flag


def user_definitely_wants_to_talk_about_game_that_user_played_request(
        ngrams, vars, additional_check=None):
    user_uttr = state_utils.get_last_human_utterance(vars)
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    game_names_from_local_list_of_games = find_games_in_text(user_uttr.get("text", ""))
    flag = bool(game_names_from_local_list_of_games) \
        and does_text_contain_link_to_gaming(bot_uttr.get("text", "")) \
        and additional_check(ngrams, vars) \
        and (
            not was_link_from_gaming_to_other_skill_made_in_previous_bot_utterance(vars)
            or was_link_from_gaming_to_other_skill_made_in_previous_bot_utterance(vars)
            and if_chat_about_particular_topic(
                user_uttr,
                compiled_pattern=GAMES_WITH_AT_LEAST_1M_COPIES_SOLD_COMPILED_PATTERN))
    logger.info(f"user_definitely_wants_to_talk_about_game_that_user_played_and_bot_didnt_play with additional check "
                f"{common_intents.get_additional_check_description(additional_check)}: {flag}")
    return flag


def user_doesnt_like_gaming_request(ngrams, vars):
    user_uttr = state_utils.get_last_human_utterance(vars)
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    bot_text = bot_uttr.get("text", "").lower()
    found_game_name = bool(find_games_in_text(user_uttr.get("text", "")))
    flag = is_no(user_uttr) \
        and not found_game_name \
        and (
            does_text_contain_link_to_gaming(bot_text)
            or common_intents.is_question_about_games(bot_text)) \
        and not was_link_from_gaming_to_other_skill_made_in_previous_bot_utterance(vars)
    logger.info(f"user_doesnt_like_gaming_request={flag}")
    return flag


def user_didnt_name_game_after_question_about_games_and_didnt_refuse_to_discuss_request(ngrams, vars):
    logger.info(f"user_didnt_name_game_after_question_about_games_and_didnt_refuse_to_discuss_request")
    user_uttr = state_utils.get_last_human_utterance(vars)
    bot_text = state_utils.get_last_bot_utterance(vars).get("text", "")
    found_game_name = bool(find_games_in_text(user_uttr.get("text", "")))
    flag = not is_no(user_uttr) \
        and not found_game_name \
        and (does_text_contain_link_to_gaming(bot_text) or common_intents.is_question_about_games(bot_text)) \
        and not was_link_from_gaming_to_other_skill_made_in_previous_bot_utterance(vars)
    logger.info(f"user_didnt_name_game_after_question_about_games_and_didnt_refuse_to_discuss_request={flag}")
    return flag


def user_wants_to_discuss_minecraft_request(ngrams, vars):
    flag = user_definitely_wants_to_talk_about_particular_game_request(
        ngrams,
        vars,
        additional_check=is_minecraft_mentioned_in_user_or_bot_uttr,
    ) or user_definitely_wants_to_talk_about_game_that_user_played_request(
        ngrams, vars, additional_check=is_minecraft_mentioned_in_user_or_bot_uttr
    ) \
        or was_link_from_gaming_to_other_skill_made_in_previous_bot_utterance(vars) \
        and if_chat_about_particular_topic(state_utils.get_last_human_utterance(vars), key_words=["minecraft"])
    logger.info(f"user_wants_to_discuss_minecraft_request={flag}")
    return flag


def user_wants_game_description_2_or_more_of_description_turns_remain_request(ngrams, vars):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    isyes = is_yes(user_uttr)
    if not isyes:
        flag = True
    logger.info(f"user_wants_game_description_2_or_more_of_description_turns_remain_request={flag}")
    return flag
