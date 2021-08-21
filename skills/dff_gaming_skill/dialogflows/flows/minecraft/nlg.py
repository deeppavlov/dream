import logging
import os
import random
import re

import sentry_sdk

import common.constants as common_constants
import common.dialogflow_framework.utils.state as state_utils
import common.gaming as common_gaming
from common.universal_templates import if_chat_about_particular_topic

import dialogflows.common.nlg as common_nlg
from dialogflows.common import shared_memory_ops
from dialogflows.common.nlg import error_handler


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))

logger = logging.getLogger(__name__)


MINECRAFT_HOW_TOS = common_gaming.load_json(os.getenv("MINECRAFT_HOW_TOS"))


@error_handler
def ask_user_when_he_started_to_play_minecraft_response(vars, candidate_game_id_is_already_set):
    shared_memory_ops.set_current_igdb_game_id_if_game_for_discussion_is_identified(
        vars, candidate_game_id_is_already_set)
    response = f"Perfect taste! Minecraft is the best game ever! I dived into the game right after I was created. "\
        f"And what about you? When did you start to play Minecraft?"
    human_uttr = state_utils.get_last_human_utterance(vars)
    bot_text = state_utils.get_last_bot_utterance(vars).get("text", "")
    state_utils.add_acknowledgement_to_response_parts(vars)
    flags_set = False
    if not if_chat_about_particular_topic(human_uttr, compiled_pattern=re.compile("minecraft", flags=re.I)):
        flags_set, response = common_nlg.maybe_set_confidence_and_continue_based_on_previous_bot_phrase(
            vars, bot_text, response)
        logger.info(f"flags_set: {flags_set}")
    if not flags_set:
        state_utils.set_confidence(vars, confidence=common_nlg.CONF_1)
        state_utils.set_can_continue(vars, continue_flag=common_constants.MUST_CONTINUE)
    return response


def tell_how_to(vars, must_continue=True):
    used_how_to_indices = state_utils.get_shared_memory(vars).get("used_how_to_indices", [])
    remaining_indices = list(set(range(len(MINECRAFT_HOW_TOS))) - set(used_how_to_indices))
    assert remaining_indices, "Function `tell_how_to` should only be called if unused how tos remain"
    i = random.choice(remaining_indices)
    state_utils.save_to_shared_memory(vars, current_how_to_index=i)
    if must_continue:
        state_utils.set_confidence(vars, confidence=common_nlg.CONF_1)
        state_utils.set_can_continue(vars, continue_flag=common_constants.MUST_CONTINUE)
    else:
        state_utils.set_confidence(vars, confidence=common_nlg.CONF_092_CAN_CONTINUE)
        state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    return MINECRAFT_HOW_TOS[i]["question_to_user"]


@error_handler
def ask_if_user_wants_to_know_how_to_response(vars, must_continue=True):
    state_utils.add_acknowledgement_to_response_parts(vars)
    return "I know another cool thing. " + tell_how_to(vars, must_continue)


@error_handler
def comment_on_user_experience_and_ask_if_user_wants_to_know_how_to_response(vars):
    uttr_text = state_utils.get_last_human_utterance(vars).get("text", "")
    experience_comment, time_detected = common_nlg.compose_experience_comment(uttr_text)
    do_you_want_how_to = tell_how_to(vars, must_continue=time_detected)
    state_utils.add_acknowledgement_to_response_parts(vars)
    return experience_comment \
        + " During one of my hacks into Minecraft I discovered a secret trick. " \
        + do_you_want_how_to


@error_handler
def tell_how_to_and_ask_if_it_was_interesting_response(vars):
    how_to_index = state_utils.get_shared_memory(vars).get("current_how_to_index")
    assert how_to_index is not None, "The shared memory field `current_how_to_index` should have been filled on one "\
        "of previous turns"
    state_utils.set_confidence(vars, confidence=common_nlg.CONF_1)
    state_utils.set_can_continue(vars, continue_flag=common_constants.MUST_CONTINUE)
    shared_memory_ops.add_how_to_index_to_used_how_to_indices(vars, how_to_index)
    return MINECRAFT_HOW_TOS[how_to_index]["answer"] + " Was it interesting?"


def tell_about_building_hogwarts_in_minecraft_ask_what_interesting_user_built(
        vars,
        must_continue=False,
):
    response = f"I had a great time building a copy of the Hogwarts castle "\
        f"from Harry Potter. What is the most interesting thing you built?"
    if must_continue:
        state_utils.set_confidence(vars, confidence=common_nlg.CONF_1)
        state_utils.set_can_continue(vars, continue_flag=common_constants.MUST_CONTINUE)
    else:
        state_utils.set_confidence(vars, confidence=common_nlg.CONF_092_CAN_CONTINUE)
        state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    return response


@error_handler
def tell_about_building_hogwarts_in_minecraft_ask_what_interesting_user_built_response(
        vars,
        must_continue=False,
        prefix=None,
):
    prefix = "" if prefix is None else prefix + " "
    return prefix + tell_about_building_hogwarts_in_minecraft_ask_what_interesting_user_built(vars, must_continue)


@error_handler
def comment_on_user_experience_and_say_build_hogwarts_phrase(vars):
    uttr_text = state_utils.get_last_human_utterance(vars).get("text", "")
    experience_comment, time_detected = common_nlg.compose_experience_comment(uttr_text)
    what_built_phrase = tell_about_building_hogwarts_in_minecraft_ask_what_interesting_user_built(
        vars,
        time_detected,
    )
    return experience_comment + " " + what_built_phrase


@error_handler
def praise_user_achievement_in_minecraft_and_try_to_link_to_harry_potter_response(vars):
    disliked_skills = state_utils.get_disliked_skills(vars)
    used_linkto_phrases_ids = shared_memory_ops.get_used_linkto_phrase_ids(vars)
    logger.info(
        f"(praise_user_achievement_in_minecraft_and_try_to_link_to_harry_potter_response)"
        f"LINKTO_RESPONSES_TO_LINKTO_IDS: {shared_memory_ops.LINKTO_RESPONSES_TO_LINKTO_IDS}"
    )
    book_link_to_id = shared_memory_ops.LINKTO_RESPONSES_TO_LINKTO_IDS[
        common_gaming.special_links_to_books["Harry Potter"][0]]
    movie_link_to_id = shared_memory_ops.LINKTO_RESPONSES_TO_LINKTO_IDS[
        common_gaming.special_links_to_movies["Harry Potter"][0]]
    if "movie_skill" not in disliked_skills and movie_link_to_id not in used_linkto_phrases_ids:
        response = "Sounds cool! " + common_gaming.special_links_to_movies['Harry Potter'][0]
        shared_memory_ops.add_used_linkto_to_shared_memory(
            vars, common_gaming.special_links_to_movies['Harry Potter'][0])
    elif "book_skill" not in disliked_skills and book_link_to_id not in used_linkto_phrases_ids:
        response = "Sounds cool! " + common_gaming.special_links_to_books['Harry Potter'][0]
        shared_memory_ops.add_used_linkto_to_shared_memory(
            vars, common_gaming.special_links_to_books['Harry Potter'][0])
    else:
        response = ""
    if response:
        state_utils.set_confidence(vars, confidence=common_nlg.CONF_09_DONT_UNDERSTAND_DONE)
        state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_NOT_CONTINUE)
    else:
        state_utils.set_confidence(vars, confidence=common_nlg.CONF_0)
        state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_NOT_CONTINUE)
    shared_memory_ops.mark_current_bot_utterance_as_link_to_other_skill(vars)
    state_utils.add_acknowledgement_to_response_parts(vars)
    return response
