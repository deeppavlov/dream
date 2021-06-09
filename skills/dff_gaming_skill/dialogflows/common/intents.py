import inspect
import logging
import os

import sentry_sdk

import common.dialogflow_framework.utils.state as state_utils
from common.gaming import GAMES_WITH_AT_LEAST_1M_COPIES_SOLD_COMPILED_PATTERN
from common.universal_templates import if_chat_about_particular_topic, if_choose_topic
from common.utils import is_yes


logger = logging.getLogger(__name__)
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))


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
    found_video_game_in_user_uttr = bool(
        GAMES_WITH_AT_LEAST_1M_COPIES_SOLD_COMPILED_PATTERN.search(user_uttr.get("text", "").lower()))
    found_video_game_in_bot_uttr = bool(
        GAMES_WITH_AT_LEAST_1M_COPIES_SOLD_COMPILED_PATTERN.search(prev_bot_uttr.get("text", "").lower()))
    choose_particular_game = if_choose_topic(user_uttr, prev_bot_uttr) and found_video_game_in_user_uttr
    question_answer_contains_video_game = "?" not in user_uttr.get("text", "") \
        and "?" in prev_bot_uttr.get("text", "") \
        and found_video_game_in_user_uttr
    bot_asked_about_game_and_user_answered_yes = found_video_game_in_bot_uttr \
        and "?" in prev_bot_uttr.get("text", "") \
        and is_yes(user_uttr)
    return lets_talk_about_game(vars) or choose_particular_game or question_answer_contains_video_game \
        or bot_asked_about_game_and_user_answered_yes


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
