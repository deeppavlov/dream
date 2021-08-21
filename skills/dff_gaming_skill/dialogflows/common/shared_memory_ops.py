import logging
import os

import sentry_sdk
from nltk.tokenize import sent_tokenize

import common.dialogflow_framework.utils.state as state_utils
import common.gaming as common_gaming

from dialogflows.common import game_info
from dialogflows.common.game_info import search_igdb_game_description_by_user_and_bot_phrases


NUM_SENTENCES_IN_ONE_TURN_OF_GAME_DESCRIPTION = 2


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))

logger = logging.getLogger(__name__)


ASSERTION_ERROR_NO_GAMES_IN_SHARED_MEMORY = (
    "Shared memory field 'igdb_game_ids_user_wanted_to_discuss' is empty. "
    "If dff_gaming_skill reached state SYS_USER_CONFIRMS_GAME 'games_user_wanted_do_discuss' cannot be empty "
)
ASSERTION_ERROR_MSG_CANDIDATE_GAME_IS_NOT_SET = (
    "This function should be called if shared memory field "
    "`candidate_game_id` is set. Shared memory field 'candidate_game_id' is supposed to be set when skill goes "
    "through states SYS_USER_MAYBE_WANTS_TO_TALK_ABOUT_PARTICULAR_GAME -> USR_CHECK_WITH_USER_GAME_TITLE and "
    "the field is supposed to be emptied when skill leaves states SYS_USER_CONFIRMS_GAME_BOT_NEVER_PLAYED, "
    "(scopes.MINECRAFT, State.USR_START), SYS_USER_CONFIRMS_GAME_BOT_NEVER_PLAYED."
)


def _build_linkto_responses_to_ids_dictionary(
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


LINKTO_RESPONSES_TO_LINKTO_IDS = _build_linkto_responses_to_ids_dictionary(
    common_gaming.links_to_movies,
    common_gaming.links_to_books,
    common_gaming.special_links_to_movies,
    common_gaming.special_links_to_books,
)


def get_igdb_ids_for_games_user_wanted_to_discuss(vars, assert_not_empty=True):
    shared_memory = state_utils.get_shared_memory(vars)
    ids = shared_memory.get("igdb_ids_for_games_user_wanted_to_discuss", [])
    if assert_not_empty:
        assert ids, (
            "Shared memory field 'igdb_game_ids_user_wanted_to_discuss' is empty. "
            "If dff_gaming_skill reached state SYS_USER_CONFIRMS_GAME 'games_user_wanted_do_discuss' cannot be empty "
        )
    return ids


def get_candidate_game_id(vars):
    shared_memory = state_utils.get_shared_memory(vars)
    logger.info(f"(get_candidate_game_id)shared_memory: {shared_memory.keys()}")
    candidate_game_id = shared_memory.get("candidate_game_id")
    return candidate_game_id


def get_current_igdb_game(vars, assert_not_empty=True):
    shared_memory = state_utils.get_shared_memory(vars)
    game_id = shared_memory.get("current_igdb_game_id", "")
    if game_id:
        game = game_info.games_igdb_ids.get(str(game_id))
        assert game is not None, (
            f"If some game is set for discussion it should have been added to `games_igdb_ids`."
            f" No game for id {repr(game_id)}."
        )
    else:
        game = None
        if assert_not_empty:
            assert game_id, (
                "Shared memory field 'current_igdb_game_id' is empty. If dff_gaming_skill reached "
                "state SYS_USER_CONFIRMS_GAME and did not reached SYS_ERR 'current_igdb_game_id' cannot be empty"
            )
    return game


def get_used_linkto_phrase_ids(vars):
    shared_memory = state_utils.get_shared_memory(vars)
    return shared_memory.get("used_linkto_phrase_ids_from_gaming", [])


def put_game_id_to_igdb_game_ids_user_wanted_to_discuss(vars, id_):
    ids = get_igdb_ids_for_games_user_wanted_to_discuss(vars, False)
    ids.append(id_)
    state_utils.save_to_shared_memory(vars, igdb_game_ids_user_wanted_to_discuss=ids)


def put_candidate_id_to_igdb_game_ids_user_wanted_to_discuss(vars):
    candidate_game_id = get_candidate_game_id(vars)
    assert candidate_game_id is not None and candidate_game_id, ASSERTION_ERROR_MSG_CANDIDATE_GAME_IS_NOT_SET
    put_game_id_to_igdb_game_ids_user_wanted_to_discuss(vars, candidate_game_id)


def clean_candidate_game_id(vars):
    state_utils.save_to_shared_memory(vars, candidate_game_id="")


def set_current_igdb_game_id_from_candidate_game_id(vars):
    logger.info("set_current_igdb_game_id_from_candidate_game_id")
    candidate_game_id = get_candidate_game_id(vars)
    assert candidate_game_id is not None and candidate_game_id, ASSERTION_ERROR_MSG_CANDIDATE_GAME_IS_NOT_SET
    state_utils.save_to_shared_memory(vars, current_igdb_game_id=candidate_game_id)


def set_current_igdb_game_id_if_game_for_discussion_is_identified(vars, candidate_game_id_is_already_set):
    if candidate_game_id_is_already_set:
        set_current_igdb_game_id_from_candidate_game_id(vars)
        put_candidate_id_to_igdb_game_ids_user_wanted_to_discuss(vars)
    else:
        igdb_game_description, _ = search_igdb_game_description_by_user_and_bot_phrases(vars)
        if igdb_game_description is not None:
            state_utils.save_to_shared_memory(vars, current_igdb_game_id=igdb_game_description["id"])
            put_game_id_to_igdb_game_ids_user_wanted_to_discuss(vars, igdb_game_description["id"])
        else:
            state_utils.save_to_shared_memory(vars, current_igdb_game_id="")
    clean_candidate_game_id(vars)


def add_used_linkto_to_shared_memory(vars, text):
    used_linkto_phrase_ids = get_used_linkto_phrase_ids(vars)
    id_ = LINKTO_RESPONSES_TO_LINKTO_IDS.get(text)
    assert id_ is not None, f"Link phrases added to shared memory has to be from `common.gaming`. Got: '{text}'"
    used_linkto_phrase_ids.append(id_)
    state_utils.save_to_shared_memory(vars, used_linkto_phrase_ids_from_gaming=used_linkto_phrase_ids)


def get_split_summary(vars):
    shared_memory = state_utils.get_shared_memory(vars)
    current_index = shared_memory.get("curr_summary_sent_index", 0)
    game = get_current_igdb_game(vars)
    summary = game.get("summary")
    assert summary is not None, (
        "Game descriptions without required keys are filtered in function "
        "`search_igdb_for_game` function. Maybe the wrong list of keys was passed to `search_igdb_for_game`, or "
        "game description was acquired some other way, or game description was modified."
    )
    sentences = sent_tokenize(summary)
    split_summary = {"sentences": sentences, "current_index": current_index}
    return split_summary


def get_next_sentences_from_summary_and_num_remaining(vars, n_sent=2):
    split_summary = get_split_summary(vars)
    i = split_summary["current_index"]
    split_summary = get_split_summary(vars)
    text = " ".join(split_summary["sentences"][i : i + n_sent])
    split_summary["current_index"] += n_sent
    num_remaining = len(split_summary["sentences"]) - split_summary["current_index"]
    state_utils.save_to_shared_memory(vars, curr_summary_sent_index=split_summary["current_index"])
    return text, num_remaining


def are_there_2_or_more_turns_left_in_game_description(ngrams, vars):
    split_summary = get_split_summary(vars)
    if split_summary:
        num_remaining_sentences = len(split_summary["sentences"]) - split_summary["current_index"]
        res = num_remaining_sentences / NUM_SENTENCES_IN_ONE_TURN_OF_GAME_DESCRIPTION > 1
    else:
        res = False
    return res


def add_how_to_index_to_used_how_to_indices(vars, i):
    shared_memory = state_utils.get_shared_memory(vars)
    indices = shared_memory.get("used_how_to_indices", [])
    indices.append(i)
    state_utils.save_to_shared_memory(vars, used_how_to_indices=indices)


def mark_current_bot_utterance_as_link_to_other_skill(vars):
    current_human_utterance_index = state_utils.get_human_utter_index(vars)
    logger.info(
        f"Bot utterance after human utterance with index {current_human_utterance_index} "
        f"is marked to link to other skill"
    )
    state_utils.save_to_shared_memory(
        vars, index_of_last_human_utterance_after_which_link_from_gaming_was_made=current_human_utterance_index
    )


def was_link_from_gaming_to_other_skill_made_in_previous_bot_utterance(vars):
    shared_memory = state_utils.get_shared_memory(vars)
    prev_active_skill = state_utils.get_last_bot_utterance(vars).get("active_skill")
    index_of_last_human_utterance_after_which_link_from_gaming_was_made = shared_memory.get(
        "index_of_last_human_utterance_after_which_link_from_gaming_was_made", -2
    )
    current_human_utterance_index = state_utils.get_human_utter_index(vars)
    diff = current_human_utterance_index - index_of_last_human_utterance_after_which_link_from_gaming_was_made
    if index_of_last_human_utterance_after_which_link_from_gaming_was_made < 0:
        logger.info(f"No link from dff_gaming_skill was done in this dialog.")
    else:
        logger.info(f"The last link from dff_gaming_skill to other skill was done {diff} turns before")
    return diff < 2 and prev_active_skill is not None and prev_active_skill == "dff_gaming_skill"
