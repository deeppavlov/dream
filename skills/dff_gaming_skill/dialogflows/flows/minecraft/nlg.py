import logging
import os

import sentry_sdk

import common.constants as common_constants
import common.dialogflow_framework.utils.state as state_utils
import common.gaming as common_gaming

import dialogflows.common.nlg as common_nlg
import dialogflows.common.shared_memory_ops as gaming_memory
from dialogflows.common.nlg import error_handler


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))

logger = logging.getLogger(__name__)


@error_handler
def tell_about_building_hogwarts_in_minecraft_ask_what_interesting_user_built_response(
        vars,
        candidate_game_id_is_already_set,
        must_continue,
):
    gaming_memory.set_current_igdb_game_id_if_game_for_discussion_is_identified(
        vars, candidate_game_id_is_already_set)
    response = f"Cool! Minecraft is the best game ever! I had a great time building a copy of the Hogwarts castle "\
        "from Harry Potter. What is the most interesting thing you built?"
    if must_continue:
        state_utils.set_confidence(vars, confidence=common_nlg.CONF_1)
        state_utils.set_can_continue(vars, continue_flag=common_constants.MUST_CONTINUE)
    else:
        state_utils.set_confidence(vars, confidence=common_nlg.CONF_092_CAN_CONTINUE)
        state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)
    return response


@error_handler
def praise_user_achievement_in_minecraft_and_try_to_link_to_harry_potter_response(vars):
    disliked_skills = state_utils.get_disliked_skills(vars)
    used_linkto_phrases_ids = gaming_memory.get_used_linkto_phrase_ids(vars)
    logger.info(
        f"(praise_user_achievement_in_minecraft_and_try_to_link_to_harry_potter_response)"
        f"LINKTO_RESPONSES_TO_LINKTO_IDS: {gaming_memory.LINKTO_RESPONSES_TO_LINKTO_IDS}"
    )
    book_link_to_id = gaming_memory.LINKTO_RESPONSES_TO_LINKTO_IDS[
        common_gaming.special_links_to_books["Harry Potter"][0]]
    movie_link_to_id = gaming_memory.LINKTO_RESPONSES_TO_LINKTO_IDS[
        common_gaming.special_links_to_movies["Harry Potter"][0]]
    if "movie_skill" not in disliked_skills and movie_link_to_id not in used_linkto_phrases_ids:
        response = "Sounds cool! " + common_gaming.special_links_to_movies['Harry Potter'][0]
        gaming_memory.add_used_linkto_to_shared_memory(vars, common_gaming.special_links_to_movies['Harry Potter'][0])
    elif "book_skill" not in disliked_skills and book_link_to_id not in used_linkto_phrases_ids:
        response = "Sounds cool! " + common_gaming.special_links_to_books['Harry Potter'][0]
        gaming_memory.add_used_linkto_to_shared_memory(vars, common_gaming.special_links_to_books['Harry Potter'][0])
    else:
        response = ""
    if response:
        state_utils.set_confidence(vars, confidence=common_nlg.CONF_09_DONT_UNDERSTAND_DONE)
        state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_NOT_CONTINUE)
    else:
        state_utils.set_confidence(vars, confidence=common_nlg.CONF_0)
        state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_NOT_CONTINUE)
    return response
