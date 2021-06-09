import json
import logging
import os

import sentry_sdk

import common.constants as common_constants
import common.dialogflow_framework.utils.state as state_utils
from common.utils import is_no

import dialogflows.common.nlg as common_nlg
import dialogflows.common.shared_memory_ops as gaming_memory
from dialogflows.common import game_info
from dialogflows.common.nlg import error_handler, error_response


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))

logger = logging.getLogger(__name__)


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


##################################################################################################################
# Load Data
##################################################################################################################

IGDB_GAME_GENRES_FOR_REPLICAS = get_igdb_id_to_name('genre', "name_for_inserting_into_replica")


@error_handler
def check_game_name_with_user_response(vars):
    logger.info(f"check_game_name_with_user_response")
    igdb_game_description, word_game_was_mentioned_in_user_phrase = \
        game_info.search_igdb_game_description_by_user_and_bot_phrases(vars)
    if igdb_game_description is not None:
        logger.info(f"(user_wants_to_talk_about_particular_game_request)saving candidate id to shared memory")
        state_utils.save_to_shared_memory(vars, candidate_game_id=igdb_game_description["id"])
        shared_memory = state_utils.get_shared_memory(vars)
        logger.info(f"(check_game_name_with_user_response)shared_memory: {shared_memory.keys()}")
        response = f"Would you like to talk about the video game {igdb_game_description['name']}?"
        if word_game_was_mentioned_in_user_phrase:
            state_utils.set_confidence(vars, confidence=common_nlg.CONF_1)
            state_utils.set_can_continue(vars, continue_flag=common_constants.MUST_CONTINUE)
        else:
            state_utils.set_confidence(vars, confidence=common_nlg.CONF_092_CAN_CONTINUE)
            state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    else:
        response = ""
        state_utils.set_confidence(vars, confidence=common_nlg.CONF_0)
        state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_NOT_CONTINUE)
    return response


@error_handler
def confess_bot_never_played_game_and_ask_user_if_he_played_response(vars, candidate_game_id_is_already_set):
    gaming_memory.set_current_igdb_game_id_if_game_for_discussion_is_identified(vars, candidate_game_id_is_already_set)
    game = gaming_memory.get_current_igdb_game(vars, assert_not_empty=False)
    if game is None:
        logger.warning(
            "No appropriate igdb game description were found. Game description could be filtered because it lacked "
            "required keys. Another cause possible cause of this situation is that local igdb saved search results "
            "do not have detected game. In such a case you should update local copy of igdb.com search results."
        )
        response = error_response(vars)
        state_utils.set_confidence(vars, confidence=common_nlg.CONF_0)
        state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_NOT_CONTINUE)
    else:
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
        state_utils.set_confidence(vars, confidence=common_nlg.CONF_1)
        state_utils.set_can_continue(vars, continue_flag=common_constants.MUST_CONTINUE)
    return response


@error_handler
def tell_about_what_bot_likes_and_ask_if_user_recommends_game_response(vars):
    game = gaming_memory.get_current_igdb_game(vars)
    response = f"That is great! Could you give me an advice? I like games in which I can create something and "\
        f"my favorite game is Minecraft. Would you recommend me to try {game['name']}?"
    state_utils.set_confidence(vars, confidence=common_nlg.CONF_092_CAN_CONTINUE)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    return response


@error_handler
def suggest_user_game_description_response(vars):
    logger.info("called suggest_user_game_description_response")
    game = gaming_memory.get_current_igdb_game(vars)
    response = f"Would you like me to tell you short description of {game['name']}?"
    human_uttr = state_utils.get_last_human_utterance(vars)
    logger.info(f"(suggest_user_game_description_response)human_uttr: {human_uttr['text']}")
    if is_no(human_uttr):
        state_utils.set_confidence(vars, confidence=common_nlg.CONF_1)
        state_utils.set_can_continue(vars, continue_flag=common_constants.MUST_CONTINUE)
    else:
        state_utils.set_confidence(vars, confidence=common_nlg.CONF_092_CAN_CONTINUE)
        state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    return response


@error_handler
def describe_game_to_user_response(vars, ask_if_user_wants_more=True):
    text, num_remaining_sentences = gaming_memory.get_next_sentences_from_summary_and_num_remaining(vars)
    if ask_if_user_wants_more:
        response = text + ".. Would you like to hear more?"
    else:
        response = text + " So. Would you like to play this game?"
    if num_remaining_sentences == 0:
        state_utils.save_to_shared_memory(vars, curr_summary_sent_index=0)
    state_utils.set_confidence(vars, confidence=common_nlg.CONF_092_CAN_CONTINUE)
    state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    return response
