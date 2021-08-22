# %%
import os
import logging
import random
import re
from copy import deepcopy
from enum import Enum, auto
from pathlib import Path

import sentry_sdk

from dff import dialogflow_extension
import common.dialogflow_framework.utils.state as state_utils
import common.dialogflow_framework.utils.condition as condition_utils

import dialogflows.scopes as scopes

from common.fact_random import get_facts
from common.constants import CAN_CONTINUE_SCENARIO, CAN_CONTINUE_PROMPT, MUST_CONTINUE, CAN_NOT_CONTINUE
from common.gaming import get_harry_potter_part_name_if_special_link_was_used
from common.movies import (
    get_movie_template,
    praise_actor,
    praise_director_or_writer_or_visuals,
    WHAT_OTHER_MOVIE_TO_DISCUSS,
    CLARIFY_WHAT_MOVIE_TO_DISCUSS,
    MOVIE_COMPILED_PATTERN,
    ABOUT_MOVIE_TITLES_PHRASES,
    DIFFERENT_SCRIPT_TEMPLATES,
    RECOMMEND_REQUEST_PATTERN,
    RECOMMEND_OFFER_PATTERN,
    RECOMMEND_OFFER_RESPONSE,
    RECOMMENDATION_PHRASES,
    REPEAT_RECOMMENDATION_PHRASES,
    WOULD_YOU_LIKE_TO_CONTINUE_TALK_ABOUT_MOVIES,
    WHAT_IS_YOUR_FAVORITE_MOMENT_PHRASES,
    WHAT_IS_YOUR_FAVORITE_MOMENT_NO_PLOT_FOUND_PHRASES,
    NOT_WATCHED_TEMPLATE,
    NOT_LIKE_NOT_WATCH_MOVIES_TEMPLATE,
    ACKNOWLEDGEMENT_LIKES_MOVIE,
)
from common.universal_templates import if_chat_about_particular_topic
from common.utils import (
    is_opinion_request,
    is_opinion_expression,
    get_not_used_template,
    find_first_complete_sentence,
    get_all_not_used_templates,
    COBOTQA_EXTRA_WORDS,
)
from nltk.tokenize import sent_tokenize
from dialogflows.flows.utils import (
    is_movie_title_question,
    LETTERS,
    recommend_movie_of_genre,
    is_book_question,
    is_game_question,
)
from dialogflows.flows.templates import MovieSkillTemplates
from dialogflows.flows.movie_plots import MoviePlots


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))

logger = logging.getLogger(__name__)


TOP_1k_FREQUENT_WORDS = Path("common/google-10000-english-no-swears.txt").open().read().splitlines()[:1000]


class State(Enum):
    USR_START = auto()

    SYS_EXTRACTED_MOVIE_TITLE = auto()
    SYS_CLARIFY_MOVIE_TITLE = auto()
    SYS_LETS_CHAT_ABOUT_MOVIES = auto()
    USR_WAS_ASKED_MOVIE_TITLE_QUESTION = auto()
    USR_WAS_REQUESTED_MOVIE_OPINION = auto()
    USR_WAS_ASKED_TO_CLARIFY_MOVIE_TITLE = auto()
    SYS_NOT_EXTRACTED_AFTER_CLARIFICATION = auto()
    SYS_USER_NOT_WATCH_MOVIE = auto()
    SYS_ASK_DO_YOU_KNOW_QUESTION = auto()
    USR_WAS_ASKED_DO_YOU_KNOW_QUESTION = auto()
    SYS_CHECK_ANSWER_TO_DO_YOU_KNOW = auto()
    SYS_GIVE_FACT_ABOUT_MOVIE = auto()
    USR_CHECK_ANSWER_TO_DO_YOU_KNOW = auto()
    USR_HAVE_YOU_HEARD_FACT = auto()
    SYS_ASK_QUESTION_ABOUT_MOVIE_TITLE = auto()
    SYS_FAQ = auto()
    USR_FAQ = auto()
    SYS_NOT_LIKE_MOVIES = auto()
    SYS_USER_REQUESTS_OPINION_ABOUT_MOVIE = auto()
    SYS_USER_EXPRESSES_OPINION_ABOUT_MOVIE_GENRE = auto()
    SYS_USER_REQUESTS_OPINION_ABOUT_MOVIE_GENRE = auto()
    SYS_MENTIONED_MOVIES = auto()

    SYS_USER_REQUESTS_MOVIE_RECOMMENDATION = auto()
    SYS_REPEAT_RECOMMENDATION = auto()
    USR_WAS_OFFERED_RECOMMENDATIONS = auto()
    USR_ASKED_HAVE_SEEN_MOVIE = auto()
    SYS_USR_WAS_ASKED_MOVIE_TITLE_QUESTION_NO_MOVIE_EXTRACTED = auto()
    SYS_USR_WAS_ASKED_MOVIE_TITLE_QUESTION_NO_MOVIE_EXTRACTED_NO_RECOM = auto()
    SYS_USR_WAS_ASKED_MOVIE_TITLE_QUESTION_AND_REFUSED = auto()

    SYS_OFFER_CONTINUE_MOVIE_TALK = auto()
    USR_WAS_OFFERED_TO_CONTINUE_MOVIE_TALK = auto()

    SYS_ERR = auto()
    USR_ERR = auto()


# %%

SUPER_CONFIDENCE = 1.0
HIGH_CONFIDENCE = 0.98
DEFAULT_CONFIDENCE = 0.95
OFFER_TALK_ABOUT_MOVIES_CONFIDENCE = 0.65
END_SCENARIO_OFFER_CONFIDENCE = 0.85
CLARIFICATION_CONFIDENCE = 0.98
NOT_SURE_CONFIDENCE = 0.5
SECOND_FACT_PROBA = 0.5
LINKTO_CONFIDENCE = 0.7
ZERO_CONFIDENCE = 0.0

templates = MovieSkillTemplates()
movieplots = MoviePlots(imdb=templates.imdb)

##################################################################################################################
# Init DialogFlow
##################################################################################################################


simplified_dialogflow = dialogflow_extension.DFEasyFilling(State.USR_START)

##################################################################################################################
##################################################################################################################
# Design DialogFlow.
##################################################################################################################
##################################################################################################################


def save_and_update_movie_titles(vars, movie_id, movie_title):
    shared_memory = state_utils.get_shared_memory(vars)
    discussed_movie_ids = shared_memory.get("discussed_movie_ids", [])
    discussed_movie_titles = shared_memory.get("discussed_movie_titles", [])

    discussed_movie_ids = list(set(discussed_movie_ids + [movie_id]))
    discussed_movie_titles = list(set(discussed_movie_titles + [movie_title]))

    state_utils.save_to_shared_memory(vars, current_movie_id=movie_id)
    state_utils.save_to_shared_memory(vars, current_movie_title=movie_title)
    state_utils.save_to_shared_memory(vars, discussed_movie_ids=discussed_movie_ids)
    state_utils.save_to_shared_memory(vars, discussed_movie_titles=discussed_movie_titles)
    return


def no_requests_request(ngrams, vars):
    flag = condition_utils.no_special_switch_off_requests(vars)

    if flag:
        logger.info(f"No special requests in user utterances")
        return True
    logger.info(f"Special requests in user utterances")
    return False


##################################################################################################################
# user did not watch movie
##################################################################################################################


def not_watched_request(ngrams, vars):
    # SYS_USER_NOT_WATCH_MOVIE
    human_uttr_text = state_utils.get_last_human_utterance(vars).get("text", "")
    if NOT_WATCHED_TEMPLATE.search(human_uttr_text):
        logger.info(f"Not watched in user utterance")
        return True
    return False


def ackn_not_watch_ask_for_another_movie_response(vars):
    # USR_WAS_ASKED_MOVIE_TITLE_QUESTION
    try:
        response = not_confident_lets_chat_about_movies_response(vars)
        return f"I've got you didn't watch this movie. {get_movie_template('lets_move_on')} {response}"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


##################################################################################################################
# user do not like movies / user do not watch movies
##################################################################################################################


def user_not_like_movies_request(ngrams, vars):
    # SYS_NOT_LIKE_MOVIES
    human_uttr_text = state_utils.get_last_human_utterance(vars).get("text", "")
    if NOT_LIKE_NOT_WATCH_MOVIES_TEMPLATE.search(human_uttr_text):
        logger.info(f"Not like movies in user utterances")
        return True
    return False


def user_not_like_movies_response(vars):
    # USR_START
    try:
        state_utils.set_confidence(vars, confidence=SUPER_CONFIDENCE)
        state_utils.set_can_continue(vars, continue_flag=CAN_NOT_CONTINUE)
        state_utils.save_to_shared_memory(vars, current_status="")
        return f"Anyway. I adore movies because for me it's almost the only opportunity to explore the human world."
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


##################################################################################################################
# user was asked about movie title
##################################################################################################################


def user_was_asked_about_movie_title(vars):
    prev_bot_uttr = state_utils.get_last_bot_utterance(vars)

    shared_memory = state_utils.get_shared_memory(vars)
    current_status = shared_memory.get("current_status", "")

    if is_movie_title_question(prev_bot_uttr) or current_status == "movie_prompt":
        return True
    return False


def user_was_asked_about_movie_title_request(ngrams, vars):
    if user_was_asked_about_movie_title(vars):
        logger.info(f"User was asked movie title question")
        return True
    return False


def user_refused_movie_title_question_request(ngrams, vars):
    if user_was_asked_about_movie_title(vars) and condition_utils.is_no_vars(vars):
        logger.info(f"User was asked movie title question AND said NO.")
        return True
    return False


def user_was_asked_about_movie_title_and_declined_recommendations_request(ngrams, vars):
    declined_recommendations_previously = state_utils.get_shared_memory(vars).get("recommendations_declined", False)
    was_asked_movie_title_question = user_was_asked_about_movie_title_request(ngrams, vars)
    if was_asked_movie_title_question and declined_recommendations_previously:
        logger.info(f"User was asked movie title question AND declined recommendations before that.")
        return True
    return False


##################################################################################################################
# let's talk about movies
##################################################################################################################


def lets_chat_about_movies_request(ngrams, vars):
    # SYS_LETS_CHAT_ABOUT_MOVIES
    # this check will also catch linkto questions about movies
    user_lets_chat_about = if_chat_about_particular_topic(
        state_utils.get_last_human_utterance(vars),
        state_utils.get_last_bot_utterance(vars),
        compiled_pattern=MOVIE_COMPILED_PATTERN,
    )

    if user_lets_chat_about:
        logger.info(f"Let's chat about movies in user utterances")
        return True
    return False


def lets_chat_about_movies_response(vars):
    # USR_ASK_MOVIE_TITLE_QUESTION
    logger.info(f"Bot asks user's opinion about movies.")
    try:
        state_utils.set_confidence(vars, confidence=SUPER_CONFIDENCE)
        state_utils.set_can_continue(vars, continue_flag=MUST_CONTINUE)
        opinion_req = random.choice(ABOUT_MOVIE_TITLES_PHRASES)
        state_utils.save_to_shared_memory(
            vars,
            used_movies_questions=state_utils.get_shared_memory(vars).get("used_movies_questions", []) + [opinion_req],
        )
        state_utils.save_to_shared_memory(vars, current_status="movie_prompt")
        return opinion_req
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


def mentioned_movies_request(ngrams, vars):
    # SYS_MENTIONED_MOVIES
    # this check if any mentions of movies in user utterance
    if MOVIE_COMPILED_PATTERN.search(state_utils.get_last_human_utterance(vars).get("text", "")):
        logger.info(f"Mentioned movies in user utterances")
        return True
    return False


def not_confident_lets_chat_about_movies_response(vars):
    # USR_ASK_MOVIE_TITLE_QUESTION
    logger.info(f"Bot asks user's opinion about movies.")
    try:
        if state_utils.get_last_bot_utterance(vars).get("active_skill", "") == "dff_movie_skill":
            prephrase = f"{get_movie_template('lets_move_on')} "
        else:
            prephrase = ""
        state_utils.set_confidence(vars, confidence=HIGH_CONFIDENCE)
        state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_PROMPT)
        opinion_req = random.choice(ABOUT_MOVIE_TITLES_PHRASES)
        state_utils.save_to_shared_memory(
            vars,
            used_movies_questions=state_utils.get_shared_memory(vars).get("used_movies_questions", []) + [opinion_req],
        )
        state_utils.save_to_shared_memory(vars, current_status="movie_prompt")
        return f"{prephrase}{opinion_req}"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


##################################################################################################################
# movie title extraction and clarification
##################################################################################################################

EXTRACTED_MENTIONS_BUFFER = {}


def extract_mentions(vars, check_full_utterance=False):
    global EXTRACTED_MENTIONS_BUFFER
    curr_human_uttr = deepcopy(state_utils.get_last_human_utterance(vars))
    curr_human_uttr_text = curr_human_uttr.get("text", "")
    harry_potter_part_name = get_harry_potter_part_name_if_special_link_was_used(
        curr_human_uttr, state_utils.get_last_bot_utterance(vars)
    )
    if harry_potter_part_name is not None:
        new_cobot_entities = {
            "entities": [harry_potter_part_name],
            "labelled_entities": [{"label": "videoname", "text": harry_potter_part_name}],
        }
        if "annotations" not in curr_human_uttr:
            curr_human_uttr["annotations"] = {}
        logger.info(
            f"For mentions extraction cobot_entities annotation "
            f"'{curr_human_uttr['annotations'].get('cobot_entities')}' is replaced with '{new_cobot_entities}'"
        )
        curr_human_uttr["annotations"]["cobot_entities"] = new_cobot_entities
    if curr_human_uttr_text in EXTRACTED_MENTIONS_BUFFER:
        movies_ids, unique_persons, mentioned_genres = EXTRACTED_MENTIONS_BUFFER[curr_human_uttr_text]
    else:
        movies_ids, unique_persons, mentioned_genres = templates.extract_mentions(
            curr_human_uttr, find_ignored=True, check_full_utterance=check_full_utterance
        )
        if len(EXTRACTED_MENTIONS_BUFFER) == 100:
            EXTRACTED_MENTIONS_BUFFER = {}
        EXTRACTED_MENTIONS_BUFFER[curr_human_uttr_text] = [movies_ids, unique_persons, mentioned_genres]
    return movies_ids, unique_persons, mentioned_genres


def extract_movie_title(vars, movies_ids):
    movie_id, movie_title = None, ""

    if len(movies_ids) > 0 and templates.imdb(movies_ids[-1]).get("title", ""):
        movie_id = movies_ids[-1]
        movie_title = templates.imdb(movie_id)["title"]
        logger.info(f"Get movie title `{movie_title}` for movie_id `{movie_id}`.")
    return movie_id, movie_title


def is_popular_movie(movie_id):
    movie_title = templates.imdb(movie_id).get("title", "")

    numvotes = templates.imdb.get_info_about_movie(movie_id, "numVotes")
    numvotes = 0 if numvotes is None else numvotes
    letters_in_title = re.search(LETTERS, movie_title)
    if numvotes >= 10000 and letters_in_title and len(letters_in_title[0]) >= 2:
        return "popular"
    elif numvotes < 10000 and letters_in_title and len(letters_in_title[0]) >= 2:
        return "known"

    return "unknown"


def is_rare_movie_title(movie_id):
    movie_title = templates.imdb(movie_id).get("title", "").lower()
    if len(movie_title.split()) > 2 or any([word not in TOP_1k_FREQUENT_WORDS for word in movie_title.split()]):
        return True
    return False


def popular_movie_title_extracted_request(ngrams, vars):
    # SYS_POPULAR_MOVIE_TITLE_EXTRACTED
    movies_ids, unique_persons, mentioned_genres = extract_mentions(vars)
    movie_id, movie_title = extract_movie_title(vars, movies_ids)

    if movie_id:
        if is_popular_movie(movie_id) == "popular":
            logger.info("Found movie title with more than 10k votes. movie_title_extracted_request found.")
            return True

    return False


def to_be_clarified_movie_title_extracted_request(ngrams, vars):
    # SYS_TO_BE_CLARIFIED_MOVIE_TITLE
    movies_ids, unique_persons, mentioned_genres = extract_mentions(vars)
    movie_id, movie_title = extract_movie_title(vars, movies_ids)
    if movie_id:
        if is_popular_movie(movie_id) == "known":
            logger.info("Found movie title with less than 10k votes. movie_title_to_be_clarified_request found.")
            return True

    return False


def movie_title_clarification_response(vars):
    # USR_MOVIE_TITLE_CLARIFICATION
    logger.info(f"Bot clarifies movie title.")
    try:
        movies_ids, unique_persons, mentioned_genres = extract_mentions(vars, check_full_utterance=True)
        movie_id, movie_title = extract_movie_title(vars, movies_ids)
        collect_and_save_facts_about_location(movie_id, vars)
        user_was_asked_for_movie_title_or_clarification = user_was_asked_about_movie_title(vars)
        user_was_asked_for_movie_title_or_clarification |= state_utils.get_shared_memory(vars).get(
            "current_status", ""
        ) in ["movie_prompt", "clarification"]
        user_said_about_movies = MOVIE_COMPILED_PATTERN.search(state_utils.get_last_human_utterance(vars)["text"])

        if len(movies_ids) == 0 and user_was_asked_for_movie_title_or_clarification:
            logger.info(
                f"Previously bot clarified movie title, no title extracted from current utterance. "
                f"Clarify as Prompt."
            )
            response = f"{get_movie_template('dont_know_movie_title_at_all')} " f"{CLARIFY_WHAT_MOVIE_TO_DISCUSS}"
            state_utils.set_confidence(vars, END_SCENARIO_OFFER_CONFIDENCE)
            state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_PROMPT)
            state_utils.save_to_shared_memory(vars, current_status="movie_prompt")
        elif user_was_asked_for_movie_title_or_clarification or user_said_about_movies:
            movie_type = templates.imdb.get_movie_type(movie_id)
            logger.info(
                f"Clarify movie title `{movie_title}` from user utterance "
                f"`{state_utils.get_last_human_utterance(vars)['text']}`."
            )
            response = (
                f"{get_movie_template('clarification_template', movie_type=movie_type)} " f"{movie_type} {movie_title}?"
            )

            numvotes = templates.imdb.get_info_about_movie(movie_title, "numVotes")
            numvotes = 0 if numvotes is None else numvotes
            if numvotes > 1000:
                state_utils.set_confidence(vars, SUPER_CONFIDENCE)
                state_utils.set_can_continue(vars, continue_flag=MUST_CONTINUE)
            else:
                state_utils.set_confidence(vars, CLARIFICATION_CONFIDENCE)
                state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)

            save_and_update_movie_titles(vars, movie_id, movie_title)
            state_utils.save_to_shared_memory(vars, current_status="clarification")
        else:
            # user wasn't asked for movie title (or to clarify it), therefore, no response here
            return error_response(vars)
        return response
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


##################################################################################################################
# movie title SECOND clarification
##################################################################################################################


def is_yes_request(ngrams, vars):
    return condition_utils.is_yes_vars(vars)


def is_no_request(ngrams, vars):
    return condition_utils.is_no_vars(vars)


def clarified_movie_title_confirmed_request(ngrams, vars):
    # SYS_CONFIRMED_CLARIFIED_MOVIE_TITLE
    movies_ids, unique_persons, mentioned_genres = extract_mentions(vars, check_full_utterance=True)
    movie_id = state_utils.get_shared_memory(vars).get("current_movie_id", [])
    is_yes = condition_utils.is_yes_vars(vars)
    is_no = condition_utils.is_no_vars(vars)
    is_clarified_second_time = any(
        [
            phrase.lower() in state_utils.get_last_bot_utterance(vars).get("text", "").lower()
            for phrase in DIFFERENT_SCRIPT_TEMPLATES["clarification_template"]
        ]
    )
    flag = False
    if is_yes:
        logger.info(f"After 1st, 2nd clarification. User confirmed movie title. Start script.")
        flag = True
    elif len(movies_ids) > 0 and not is_no:
        movies_ids = [mid for mid in movies_ids if mid != movie_id]
        if not is_clarified_second_time and len(movies_ids) == 0:
            logger.info(f"After 1st clarification. Extracted the same movie title. Start script.")
            flag = True
        elif not is_clarified_second_time:
            # logger.info(f"After 1st clarification. Extracted another movie title. Clarify for the second time.")
            pass
        else:
            logger.info(f"After 2nd clarification. Extracted the same or another movie title. Start script.")
            flag = True
    return flag


def clarify_movie_title_again_request(ngrams, vars):
    # SYS_CLARIFY_MOVIE_TITLE_AGAIN
    movies_ids, unique_persons, mentioned_genres = extract_mentions(vars, check_full_utterance=True)
    movie_id = state_utils.get_shared_memory(vars).get("current_movie_id", [])
    is_yes = condition_utils.is_yes_vars(vars)
    is_no = condition_utils.is_no_vars(vars)
    is_clarified_second_time = any(
        [
            phrase.lower() in state_utils.get_last_bot_utterance(vars).get("text", "").lower()
            for phrase in DIFFERENT_SCRIPT_TEMPLATES["clarification_template"]
        ]
    )
    flag = False
    if is_yes:
        # logger.info(f"After 1st, 2nd clarification. User confirmed movie title. Start script.")
        pass
    elif len(movies_ids) > 0 and not is_no:
        movies_ids = [mid for mid in movies_ids if mid != movie_id]
        if not is_clarified_second_time and len(movies_ids) == 0:
            # logger.info(f"After 1st clarification. Extracted the same movie title. Start script.")
            pass
        elif not is_clarified_second_time:
            logger.info(f"After 1st clarification. Extracted another movie title. Clarify for the second time.")
            flag = True
        else:
            # logger.info(f"After 2nd clarification. Extracted the same or another movie title. Start script.")
            pass
    elif is_no:
        logger.info(f"After 1st, 2nd clarification. User rejects offered movie title.")
        if len(movies_ids) > 0:
            movies_ids = [mid for mid in movies_ids if mid != movie_id]
            if len(movies_ids) == 0:
                # logger.info(f"After 1st, 2nd clarification. Extracted the same movie title. "
                #             f"Offer talk about movies.")
                pass
            else:
                logger.info(
                    f"After 1st, 2nd clarification. Extracted another movie title. " f"Clarify for the second time."
                )
                flag = True
        elif not is_clarified_second_time:
            logger.info(
                f"After 1st clarification. Didn't extracted movie title. " f"Ask for title for the second time."
            )
            flag = True
    return flag


def did_not_extracted_movie_title_after_clarification_request(ngrams, vars):
    # SYS_NOT_EXTRACTED_MOVIE_TITLE_AFTER_CLARIFICATION
    movies_ids, unique_persons, mentioned_genres = extract_mentions(vars, check_full_utterance=True)
    movie_id = state_utils.get_shared_memory(vars).get("current_movie_id", [])
    is_yes = condition_utils.is_yes_vars(vars)
    is_no = condition_utils.is_no_vars(vars)
    is_clarified_second_time = any(
        [
            phrase.lower() in state_utils.get_last_bot_utterance(vars).get("text", "").lower()
            for phrase in DIFFERENT_SCRIPT_TEMPLATES["clarification_template"]
        ]
    )
    flag = False
    if is_yes:
        # logger.info(f"After 1st, 2nd clarification. User confirmed movie title. Start script.")
        pass
    elif len(movies_ids) > 0 and not is_no:
        pass
    elif is_no:
        logger.info(f"After 1st, 2nd clarification. User rejects offered movie title.")
        if len(movies_ids) > 0:
            movies_ids = [mid for mid in movies_ids if mid != movie_id]
            if len(movies_ids) == 0:
                logger.info(
                    f"After 1st, 2nd clarification. Extracted the same movie title. " f"Offer talk about movies."
                )
                flag = True
            else:
                # logger.info(f"After 1st, 2nd clarification. Extracted another movie title. "
                #             f"Clarify for the second time.")
                pass
        elif not is_clarified_second_time:
            # logger.info(f"After 1st clarification. Didn't extracted movie title. "
            #             f"Ask for title for the second time.")
            pass
        else:
            logger.info(f"After 2nd clarification. Didn't extracted movie title. Stop at all.")
            flag = True
    else:
        logger.info(f"After 1st, 2nd clarification. Not yes, not no, no movie titles extracted. Stop at all.")
        flag = True
    return flag


##################################################################################################################
# movie title opinion
##################################################################################################################


def praise_random_actor_from_cast(movie_id, top_n_actors=2):
    genres = templates.imdb.get_info_about_movie(movie_id, field="genre")
    actors = templates.imdb.get_info_about_movie(movie_id, field="actors")
    if actors and len(actors) > 1:
        actor = random.choice(actors[1:top_n_actors])
        phrase = praise_actor(actor, animation="Animation" in genres)
    else:
        phrase = "This movie is definitely worth watching."
    return phrase


def movie_request_opinion_response(vars):
    # USR_MOVIE_REQUEST_OPINION
    logger.info(f"Bot asks user's opinion about the movie.")
    try:
        user_was_asked_for_movie_title_or_clarification = user_was_asked_about_movie_title(vars)
        user_was_asked_for_movie_title_or_clarification |= state_utils.get_shared_memory(vars).get(
            "current_status", ""
        ) in ["movie_prompt", "clarification", "movie_recommendation"]
        user_was_asked_for_movie_title_or_clarification |= bool(
            MOVIE_COMPILED_PATTERN.search(state_utils.get_last_human_utterance(vars).get("text", ""))
        )

        movies_ids, unique_persons, mentioned_genres = extract_mentions(
            vars, check_full_utterance=user_was_asked_for_movie_title_or_clarification
        )
        movie_id, movie_title = extract_movie_title(vars, movies_ids)
        collect_and_save_facts_about_location(movie_id, vars)
        is_popular_movie_found = is_popular_movie(movie_id) == "popular" and is_rare_movie_title(movie_id)

        if user_was_asked_for_movie_title_or_clarification or is_popular_movie_found:
            prev_status = state_utils.get_shared_memory(vars).get("current_status", "")
            if prev_status in ["clarification", "movie_recommendation"]:
                movie_id = state_utils.get_shared_memory(vars).get("current_movie_id", "")
                movie_title = state_utils.get_shared_memory(vars).get("current_movie_title", "")

            movie_type = templates.imdb.get_movie_type(movie_id)
            logger.info(f"Opinion expression and opinion request for {movie_type} title `{movie_title}`.")

            reply, _, confidence = templates.give_opinion_about_movie([movie_id])
            if confidence >= 0.9 and len(reply) > 0 and len(movie_title) > 0:
                actor_compliment = praise_random_actor_from_cast(movie_id)
                response = (
                    f"{reply} {actor_compliment} "
                    f"{get_movie_template('opinion_request_about_movie', movie_type=movie_type)}"
                )
                if user_was_asked_for_movie_title_or_clarification:
                    # super conf only if user was asked of movie OR mentioned special movie words
                    state_utils.set_confidence(vars, SUPER_CONFIDENCE)
                    state_utils.set_can_continue(vars, continue_flag=MUST_CONTINUE)
                else:
                    state_utils.set_confidence(vars, HIGH_CONFIDENCE)
                    state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_PROMPT)

                save_and_update_movie_titles(vars, movie_id, movie_title)
                state_utils.save_to_shared_memory(vars, current_status="opinion_request")

                if is_book_question(state_utils.get_last_human_utterance(vars)):
                    response = f"I've not read that book but I saw the movie. {response}"
                elif is_game_question(state_utils.get_last_human_utterance(vars)):
                    response = f"I've not played that game but I saw the movie. {response}"

            else:
                response = (
                    f"{get_movie_template('dont_know_movie_title_at_all', movie_type=movie_type)} "
                    f"{WHAT_OTHER_MOVIE_TO_DISCUSS}"
                )
                state_utils.set_confidence(vars, END_SCENARIO_OFFER_CONFIDENCE)
                state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_PROMPT)
                state_utils.save_to_shared_memory(vars, current_status="movie_prompt")
                # we don't update used questions because we use universal What other movie to discuss question
        else:
            response = error_response(vars)
        return response
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


##################################################################################################################
# do you know questions
##################################################################################################################


def ask_do_you_know_question_response(vars):
    # USR_WAS_ASKED_DO_YOU_KNOW_QUESTION
    try:
        movie_id = state_utils.get_shared_memory(vars).get("current_movie_id", "")
        movie_title = state_utils.get_shared_memory(vars).get("current_movie_title", "")
        movie_type = templates.imdb.get_movie_type(movie_id)
        collect_and_save_facts_about_location(movie_id, vars)
        discussed_movie_ids = state_utils.get_shared_memory(vars).get("discussed_movie_ids", [])

        quest_types = ["like_genres", "like_actor", "genre", "cast"]
        question_type = quest_types[len(discussed_movie_ids) % len(quest_types)]
        logger.info(f"Asking question about `{movie_title}` of type `{question_type}`.")

        if question_type == "cast":
            response = f"Do you know who are the leading actors of the {movie_type} {movie_title}?"
        elif question_type == "genre":
            response = f"Do you know the genre of the {movie_type} {movie_title}?"
        elif question_type == "like_genres":
            result = templates.imdb.get_info_about_movie(movie_title, "genre")
            if result is not None and len(result) > 0 and len(result[0]) > 0:
                result = f", {' and '.join(result[:2])}"
                response = f"Do you like the genres of this {movie_type}{result}?"
            else:
                response = f"Do you like the genres of this {movie_type}?"
        elif question_type == "like_actor":
            actors = templates.imdb.get_info_about_movie(movie_title, "actors")
            characters = templates.imdb.get_info_about_movie(movie_title, "characters")
            if actors is not None and len(actors) > 0 and characters and len(characters) > 0:
                response = f"What do you think about {actors[0]} who played {characters[0]} in this {movie_type}?"
            elif actors is not None and len(actors) > 0:
                response = f"What do you think about {actors[0]} who played the main role in this {movie_type}?"

            elif characters and len(characters) > 0:
                response = f"What do you think about {characters[0]} character in this {movie_type}?"
            else:
                response = f"Who is your favorite character in this {movie_type}?"
        else:
            response = ""
        if response:
            state_utils.set_confidence(vars, HIGH_CONFIDENCE)
            state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
            state_utils.save_to_shared_memory(vars, current_status="do_you_know_question")

            sentiment = state_utils.get_human_sentiment(vars)
            directors = templates.imdb.get_info_about_movie(movie_id, "directors")
            writers = templates.imdb.get_info_about_movie(movie_id, "writers")
            if sentiment == "positive" and directors and writers:
                director = directors[0]
                writer = writers[0]
                praise_to_director_or_writer_or_visuals = praise_director_or_writer_or_visuals(director, writer)
            else:
                praise_to_director_or_writer_or_visuals = ""

            if sentiment == "positive":
                ack = random.choice(ACKNOWLEDGEMENT_LIKES_MOVIE)
                state_utils.add_acknowledgement_to_response_parts(vars)
            else:
                ack = get_movie_template("user_opinion_comment", subcategory=sentiment, movie_type=movie_type)

            response = f"{ack} {praise_to_director_or_writer_or_visuals} {response}"
        else:
            logger.info(f"No appropriate info for Do you know question found. Ask for another movie.")
            response = not_confident_lets_chat_about_movies_response(vars)
        return response
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


def do_you_know_question_need_to_be_checked_request(ngrams, vars):
    # SYS_CHECK_ANSWER_TO_DO_YOU_KNOW
    prev_bot_uttr_text = state_utils.get_last_bot_utterance(vars).get("text", "")
    prev_status = state_utils.get_shared_memory(vars).get("current_status", "")

    if prev_status == "do_you_know_question" and "Do you know " in prev_bot_uttr_text:
        logger.info(f"Answer to Do you know question to be checked")
        return True
    return False


def check_answer_to_do_you_know_question_response(vars):
    # USR_CHECK_ANSWER_TO_DO_YOU_KNOW
    try:
        movie_id = state_utils.get_shared_memory(vars).get("current_movie_id", "")
        movie_title = state_utils.get_shared_memory(vars).get("current_movie_title", "")
        movie_type = templates.imdb.get_movie_type(movie_id)

        movies_ids, unique_persons, mentioned_genres = extract_mentions(vars)

        question_text = state_utils.get_last_bot_utterance(vars).get("text", "")
        logger.info(f"Check user's answer to do-you-know question about `{movie_title}`: `{question_text}`.")

        is_yes = condition_utils.is_yes_vars(vars)
        is_no = condition_utils.is_no_vars(vars)
        is_do_not_know = condition_utils.is_do_not_know_vars(vars)

        if "who are the leading actors" in question_text:
            result = templates.imdb.get_info_about_movie(movie_title, "actors")
            if result is not None:
                result = f"The leading actors are {', '.join(result)}."
            else:
                result = get_facts(f"who stars in {movie_type} {movie_title}?")
            if len(unique_persons) > 0 and all([name in result for name in list(unique_persons.keys())]):
                if len(unique_persons) > 1:
                    response = "Great! All those people are from main cast."
                else:
                    response = "Great! This person is from main cast."
            elif is_yes:
                if "Sorry, I don't know" in result or len(result.strip()) == 0:
                    response = f"Great! {result}"
                else:
                    response = f"Great!"
            elif is_no or is_do_not_know:
                if "Sorry, I don't know" in result or len(result.strip()) == 0:
                    response = f"Seems like I also can't find this information."
                else:
                    response = f"{result}"
            else:
                if "Sorry, I don't know" in result or len(result.strip()) == 0:
                    response = f"Never mind, I can't verify this information now."
                else:
                    response = f"Oops! No. {result}"
        elif "the genre of the" in question_text:
            result = templates.imdb.get_info_about_movie(movie_title, "genre")
            if result is not None and len(result) > 0 and len(result[0]) > 0:
                if len(result) == 1:
                    result = f"The genre of the {movie_type} is {', '.join(result)}."
                else:
                    result = f"The genres of the {movie_type} are {', '.join(result)}."
            else:
                result = get_facts(f"genre of {movie_type} {movie_title}?")
            if len(mentioned_genres) > 0 and any([name in result for name in mentioned_genres]):
                response = f"Great! {result}"
            elif is_yes:
                if "Sorry, I don't know" in result or len(result.strip()) == 0:
                    response = f"Great!"
                else:
                    response = f"Great! {result}"
            elif is_no or is_do_not_know:
                if "Sorry, I don't know" in result or len(result.strip()) == 0:
                    response = f"Seems like I also can't find this information."
                else:
                    response = f"{result}"
            else:
                if "Sorry, I don't know" in result or len(result.strip()) == 0:
                    response = f"Never mind, I can't verify this information now."
                else:
                    response = f"Oops! No. {result}"
        else:
            response = f"Never mind, I can't verify this information now."

        state_utils.set_confidence(vars, HIGH_CONFIDENCE)
        state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
        state_utils.save_to_shared_memory(vars, current_status="comment_to_question")

        return response

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


##################################################################################################################
# fact about movie
##################################################################################################################


def collect_and_save_facts_about_location(movie_id, vars):
    if movie_id:
        shared_memory = state_utils.get_shared_memory(vars)

        movie_title = templates.imdb(movie_id)["title"]
        movie_type = templates.imdb.get_movie_type(movie_id)
        facts_about_movies = shared_memory.get("facts_about_movies", {})

        if (
            facts_about_movies.get("movie_title", "") == movie_title
            and facts_about_movies.get("facts", [])
            and movie_title != "movie"
        ):
            facts_about_movies = facts_about_movies.get("facts", [])
        else:
            # random facts
            facts_about_movies = state_utils.get_fact_for_particular_entity_from_human_utterance(vars, movie_title)
            # fact_retrieval facts
            for fact in state_utils.get_facts_from_fact_retrieval(vars):
                if movie_title.lower() in fact.lower() and MOVIE_COMPILED_PATTERN.search(fact):
                    # if fact contains movie title and some movie-related words, add this fact to considered
                    facts_about_movies += [fact]

        if len(movie_title) > 0 and len(facts_about_movies) == 0:
            facts_about_movies = [get_facts(f"fact about {movie_type} {movie_title}")]

        used_facts = shared_memory.get("used_facts", [])
        facts_about_movies = get_all_not_used_templates(used_facts, facts_about_movies)
        facts_about_movies = [COBOTQA_EXTRA_WORDS.sub("", fact).strip() for fact in facts_about_movies if len(fact)]

        if len(facts_about_movies):
            state_utils.save_to_shared_memory(
                vars, facts_about_movies={"movie_title": movie_title, "facts": sorted(facts_about_movies)}
            )
    else:
        facts_about_movies = []
    return facts_about_movies


def give_more_fact_request(ngrams, vars):
    # SYS_GIVE_FACT_ABOUT_MOVIE
    prev_status = state_utils.get_shared_memory(vars).get("current_status", "")

    flag = True
    if prev_status == "fact" and len(vars["agent"]["dialog"]["human_utterances"]) > 2:
        # we want to get prev prev status to not give fact more than twice
        prev_prev_human_hyps = vars["agent"]["dialog"]["human_utterances"][-3]["hypotheses"]
        for hyp in prev_prev_human_hyps:
            if (
                hyp["skill_name"] == "dff_movie_skill"
                and hyp["dff_movie_skill_state"].get("shared_memory", {}).get("current_status", "") == "fact"
            ):
                # we have already said 2 facts, no more facts!
                flag = False
    if flag:
        logger.info(f"User was offered facts before, so offer more facts")
    return flag


def generate_fact_from_cobotqa_response(vars):
    # USR_HAVE_YOU_HEARD_FACT
    try:
        movie_id = state_utils.get_shared_memory(vars).get("current_movie_id", "")
        movie_title = state_utils.get_shared_memory(vars).get("current_movie_title", "")
        movie_type = templates.imdb.get_movie_type(movie_id)
        facts_about_movies = collect_and_save_facts_about_location(movie_id, vars)
        used_facts = state_utils.get_shared_memory(vars).get("used_facts", [])

        fact = random.choice(facts_about_movies) if len(facts_about_movies) else ""
        logger.info(f"Generated fact about {movie_type} `{movie_title}`: {fact}.")
        if len(fact) > 0:
            # save original version of used fact
            state_utils.save_to_shared_memory(vars, used_facts=used_facts + [fact])
            sentences = sent_tokenize(fact.replace(".,", "."))
            if len(sentences[0]) < 100 and "fact about" in sentences[0]:
                fact = " ".join(sentences[1:3])
            else:
                fact = " ".join(sentences[:2])

            response = f"{get_movie_template('can_you_imagine')} {fact}"
            state_utils.set_confidence(vars, HIGH_CONFIDENCE)
            state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
            state_utils.save_to_shared_memory(vars, current_status="fact")
        else:
            logger.info(f"No appropriate fact found. Offer recommendations.")
            response = bot_offers_movie_recommendation_response(vars)

        return response

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


##################################################################################################################
# FAQ about movies
##################################################################################################################


def faq_request(ngrams, vars):
    # SYS_FAQ
    response, _, _ = templates.faq(vars["agent"]["dialog"])
    if response:
        logger.info(f"Movie FAQ request")
        return True

    return False


def faq_response(vars):
    # USR_FAQ
    try:
        response, result, confidence = templates.faq(vars["agent"]["dialog"])
        if response:
            if confidence == 1:
                state_utils.set_confidence(vars, SUPER_CONFIDENCE)
                state_utils.set_can_continue(vars, continue_flag=MUST_CONTINUE)
            else:
                state_utils.set_confidence(vars, confidence)
                state_utils.set_can_continue(vars, continue_flag=CAN_NOT_CONTINUE)

            state_utils.save_to_shared_memory(vars, current_status="faq")
        else:
            state_utils.set_confidence(vars, ZERO_CONFIDENCE)
            response = error_response(vars)
            state_utils.save_to_shared_memory(vars, current_status="")

        return response

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


##################################################################################################################
# user expresses opinion (not being asked so) about movies
##################################################################################################################


def opinion_expression_about_popular_movie_request(ngrams, vars):
    # SYS_ASK_DO_YOU_KNOW_QUESTION
    movies_ids, unique_persons, mentioned_genres = extract_mentions(
        vars, check_full_utterance=user_was_asked_about_movie_title(vars)
    )
    expressed_opinion = is_opinion_expression(state_utils.get_last_human_utterance(vars))
    attitude = state_utils.get_human_sentiment(vars)

    if expressed_opinion and movies_ids:
        movie_id = movies_ids[-1]
        response, _, _ = templates.get_user_opinion(vars["agent"]["dialog"], attitude)
        if is_popular_movie(movie_id) == "popular" and response:
            logger.info(f"Current user utterance is opinion expression about popular movie.")
            return True

    return False


# def opinion_expression_about_known_movie_request(ngrams, vars):
#     # SYS_CLARIFY_MOVIE_TITLE
#     # TODO: пока что мы уточняем название и потом заново спрашиваем нравится ли пользователю фильм
#     movies_ids, unique_persons, mentioned_genres = extract_mentions(vars)
#     expressed_opinion = is_opinion_expression(state_utils.get_last_human_utterance(vars))
#     attitude = state_utils.get_human_sentiment(vars)
#
#     if expressed_opinion and movies_ids:
#         movie_id = movies_ids[-1]
#         response, _, _ = templates.get_user_opinion(vars["agent"]["dialog"], attitude)
#         if is_popular_movie(movie_id) == "known" and response:
#             logger.info(f"Current user utterance is opinion expression about known movie.")
#             return True
#
#     return False


# def opinion_expression_about_movie_persons_request(ngrams, vars):
#     # TODO: пока игнорирую, потмоу что есть gossip skill для этого случая
#     movies_ids, unique_persons, mentioned_genres = extract_mentions(vars)
#     expressed_opinion = is_opinion_expression(state_utils.get_last_human_utterance(vars))
#     attitude = state_utils.get_human_sentiment(vars)
#
#     if expressed_opinion and unique_persons:
#         response, _, _ = templates.get_user_opinion(vars["agent"]["dialog"], attitude)
#         if response:
#             logger.info(f"Current user utterance is opinion expression about movie persons.")
#             return True
#
#     return False


def opinion_expression_about_movie_genres_request(ngrams, vars):
    # SYS_USER_EXPRESSES_OPINION_ABOUT_MOVIE_GENRE
    movies_ids, unique_persons, mentioned_genres = extract_mentions(vars)
    expressed_opinion = is_opinion_expression(state_utils.get_last_human_utterance(vars))
    attitude = state_utils.get_human_sentiment(vars)

    if expressed_opinion and mentioned_genres:
        response, _, _ = templates.get_user_opinion(vars["agent"]["dialog"], attitude)
        if response:
            logger.info(f"Current user utterance is opinion expression about movie genres.")
            return True

    return False


def opinion_expression_about_movie_genres_response(vars):
    # USR_WAS_ASKED_MOVIE_TITLE_QUESTION
    try:
        movies_ids, unique_persons, mentioned_genres = extract_mentions(vars)
        response = f"What is the recent {mentioned_genres[-1]} movie you've watched?"
        state_utils.set_confidence(vars, HIGH_CONFIDENCE)
        state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_PROMPT)
        state_utils.save_to_shared_memory(vars, current_status="movie_prompt")
        return response

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


##################################################################################################################
# user expresses opinion without question about movies
##################################################################################################################


def opinion_requests_about_movie_request(ngrams, vars):
    # SYS_USER_REQUESTS_OPINION_ABOUT_MOVIE
    movies_ids, unique_persons, mentioned_genres = extract_mentions(
        vars, check_full_utterance=user_was_asked_about_movie_title(vars)
    )
    expressed_opinion = is_opinion_request(state_utils.get_last_human_utterance(vars))

    if expressed_opinion and movies_ids:
        movie_id = movies_ids[-1]
        response, _, _ = templates.give_opinion(vars["agent"]["dialog"])
        if is_popular_movie(movie_id) in ["popular", "known"] and response:
            logger.info(f"Current user utterance is opinion request about popular movie.")
            return True

    return False


def bot_express_opinion_and_ask_user_response(vars):
    # USR_WAS_REQUESTED_MOVIE_OPINION
    try:
        movies_ids, unique_persons, mentioned_genres = extract_mentions(
            vars, check_full_utterance=user_was_asked_about_movie_title(vars)
        )
        movie_id, movie_title = extract_movie_title(vars, movies_ids)
        collect_and_save_facts_about_location(movie_id, vars)

        # express opinion and request opinion about last mentioned movie in user uttr
        response = movie_request_opinion_response(vars)

        if is_popular_movie(movie_id) == "popular":
            state_utils.set_confidence(vars, SUPER_CONFIDENCE)
            state_utils.set_can_continue(vars, continue_flag=MUST_CONTINUE)
        else:
            state_utils.set_confidence(vars, HIGH_CONFIDENCE)
            state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
        save_and_update_movie_titles(vars, movie_id, movie_title)
        state_utils.save_to_shared_memory(vars, current_status="opinion_request")
        return response

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


##################################################################################################################
# user requests opinion about genres
##################################################################################################################


def opinion_requests_about_genre_request(ngrams, vars):
    # SYS_USER_REQUESTS_OPINION_ABOUT_MOVIE_GENRE
    movies_ids, unique_persons, mentioned_genres = extract_mentions(vars)
    expressed_opinion = is_opinion_request(state_utils.get_last_human_utterance(vars))

    if expressed_opinion and mentioned_genres:
        response, _, _ = templates.give_opinion(vars["agent"]["dialog"])
        if response:
            logger.info(f"Current user utterance is opinion request about movie genre.")
            return True

    return False


def bot_express_opinion_about_genre_and_ask_user_response(vars):
    # USR_WAS_ASKED_MOVIE_TITLE_QUESTION
    try:
        movies_ids, unique_persons, mentioned_genres = extract_mentions(vars)
        genre = mentioned_genres[-1]
        # express opinion about last mentioned genre in user uttr
        response, _, _ = templates.give_opinion(vars["agent"]["dialog"])
        # ask for movie with last mentioned genre in user uttr
        response = f"{response} By the way, What is the last {genre} movie you've watched?"

        state_utils.set_confidence(vars, HIGH_CONFIDENCE)
        state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_PROMPT)
        state_utils.save_to_shared_memory(vars, current_status="movie_prompt")
        return response

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


##################################################################################################################
# user requests recommendations
##################################################################################################################


def construct_movie_type_and_title(movie_id, genre=None):
    genre = genre if genre is not None else templates.imdb.get_info_about_movie(movie_id, "genre")
    genre = genre[0] if isinstance(genre, list) and len(genre) > 0 else genre
    movie_title = templates.imdb(movie_id)["title"]

    genre_movies = f"{genre} movie" if genre.lower() != "series" else "series"
    # asking whether user have seen this movie
    return f"{genre_movies} {movie_title}"


def fill_templates_with_movie_info(response, movie_id, genre=None):
    response = response.replace("MOVIE", construct_movie_type_and_title(movie_id, genre=genre))

    rating = templates.imdb.get_info_about_movie(movie_id, "imdb_rating")
    response = response.replace("RATING", str(rating) if rating else "high")

    numvotes = templates.imdb.get_info_about_movie(movie_id, "numVotes")
    if numvotes and numvotes > 1000000:
        numvotes = f"{int(numvotes / 1000000)} million"
    elif numvotes and numvotes > 1000:
        numvotes = f"{int(numvotes / 1000)} thousand"
    elif numvotes and numvotes > 100:
        numvotes = f"{int(numvotes / 100)} hundred"
    else:
        numvotes = "dozens"
    response = response.replace("NUM_VOTES", numvotes)

    year = str(templates.imdb.get_info_about_movie(movie_id, "startYear"))
    # разделяем, чтобы произнести нормально на английском год.
    response = response.replace("YEAR", f"{year[:2]} {year[2:]}" if year else "the recent past")
    return response


def recommendations_requested(vars):
    recom_request = RECOMMEND_REQUEST_PATTERN.search(state_utils.get_last_human_utterance(vars)["text"])
    recom_offer = RECOMMEND_OFFER_PATTERN.search(state_utils.get_last_bot_utterance(vars).get("text", ""))
    user_agrees = condition_utils.is_yes_vars(vars)

    if recom_request or (recom_offer and user_agrees):
        logger.info(f"User wants to get movies recommendations.")
        return True
    return False


def recommendations_request(ngrams, vars):
    # SYS_USER_REQUESTS_MOVIE_RECOMMENDATION
    if recommendations_requested(vars):
        logger.info(f"User requests movie recommendations")
        return True
    return False


def recommendations_declined(vars):
    recom_offer = RECOMMEND_OFFER_PATTERN.search(state_utils.get_last_bot_utterance(vars).get("text", ""))
    user_disagrees = condition_utils.is_no_vars(vars)

    if recom_offer and user_disagrees:
        logger.info(f"User doesn't want to get movies recommendations.")
        return True
    return False


def recommendations_declined_request(ngrams, vars):
    if recommendations_declined(vars):
        logger.info(f"User declined movie recommendations")
        return True
    return False


def which_genre_movie_to_recommend(vars):
    shared_memory = state_utils.get_shared_memory(vars)
    discussed_movie_ids = shared_memory.get("discussed_movie_ids", [])
    movies_ids, unique_persons, mentioned_genres = extract_mentions(
        vars, check_full_utterance=user_was_asked_about_movie_title(vars)
    )
    if len(mentioned_genres):
        # recommend movie of particular genre
        genre = mentioned_genres[-1]
        genre_movies = f"{genre} movies" if genre.lower() != "series" else "series"
        which_genre = "mentioned"
    else:
        # recommend movie
        age = state_utils.get_age_group(vars)
        if len(discussed_movie_ids):
            genre = templates.imdb.get_info_about_movie(discussed_movie_ids[-1], "genre")
            genre = genre[0] if len(genre) > 0 and len(genre[0]) > 0 else "Comedy"
        else:
            if age == "kid":
                genre = "Animation"
            else:
                genre = "Comedy"

        genre_movies = "movies"
        which_genre = "offered"
    return genre, genre_movies, which_genre


def bot_recommends_movie_response(vars):
    # USR_ASKED_HAVE_SEEN_MOVIE
    try:
        shared_memory = state_utils.get_shared_memory(vars)
        discussed_movie_ids = shared_memory.get("discussed_movie_ids", [])
        genre, genre_movies, _ = which_genre_movie_to_recommend(vars)

        movie_id_to_recommend = recommend_movie_of_genre(genre, discussed_movie_ids=discussed_movie_ids)
        if movie_id_to_recommend:
            movie_title_to_recommend = templates.imdb(movie_id_to_recommend)["title"]
            used_recommendation_phrases = shared_memory.get("used_recommendation_phrases", [])
            response = get_not_used_template(used_recommendation_phrases, RECOMMENDATION_PHRASES)
            state_utils.save_to_shared_memory(
                vars, used_recommendation_phrases=used_recommendation_phrases + [response]
            )
            # asking whether user have seen this movie
            response = fill_templates_with_movie_info(response, movie_id_to_recommend, genre=genre)
            # update discussed movies and current discussed movie
            save_and_update_movie_titles(vars, movie_id_to_recommend, movie_title_to_recommend)
            state_utils.save_to_shared_memory(vars, current_status="movie_recommendation")
        else:
            response = (
                f"Sorry, seems like I have no more recommendations of {genre_movies}. "
                f"What movie can you recommend to me?"
            )
            state_utils.save_to_shared_memory(vars, current_status="movie_prompt")

        if recommendations_requested(vars):
            state_utils.set_confidence(vars, SUPER_CONFIDENCE)
            state_utils.set_can_continue(vars, continue_flag=MUST_CONTINUE)
        else:
            state_utils.set_confidence(vars, HIGH_CONFIDENCE)
            state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)

        return response

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


def bot_offers_movie_recommendation_response(vars):
    # USR_WAS_OFFERED_RECOMMENDATIONS
    try:
        shared_memory = state_utils.get_shared_memory(vars)
        _, genre_movies, which_genre = which_genre_movie_to_recommend(vars)

        used_offer_recommendation_phrases = shared_memory.get("used_offer_recommendation_phrases", [])
        recom_offer = get_not_used_template(used_offer_recommendation_phrases, RECOMMEND_OFFER_RESPONSE)
        state_utils.save_to_shared_memory(
            vars, used_offer_recommendation_phrases=used_offer_recommendation_phrases + [recom_offer]
        )
        state_utils.save_to_shared_memory(vars, current_status="offer_movie_recommendation")

        _user_was_asked_about_movie_title = user_was_asked_about_movie_title(vars)
        if (
            _user_was_asked_about_movie_title
            and condition_utils.no_special_switch_off_requests(vars)
            and len(used_offer_recommendation_phrases) == 0
        ):
            # user was asked some movie title question and the answer does not contain movie title.
            state_utils.set_confidence(vars, SUPER_CONFIDENCE)
            state_utils.set_can_continue(vars, continue_flag=MUST_CONTINUE)
        else:
            state_utils.set_confidence(vars, HIGH_CONFIDENCE)
            state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)

        if _user_was_asked_about_movie_title:
            response = get_movie_template("dont_know_movie_title_at_all")
        else:
            response = ""

        if which_genre == "mentioned":
            return f"{response} {recom_offer.replace('MOVIE', genre_movies)}".strip()
        elif len(used_offer_recommendation_phrases) > 0:
            # we have already offered recommendations
            return f"{response} {recom_offer.replace('a MOVIE', 'one more movie')}".strip()
        else:
            return f"{response} {recom_offer.replace('MOVIE', 'movie')}".strip()

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


def bot_repeats_movie_recommends_and_offers_more_recomends_response(vars):
    # USR_WAS_OFFERED_RECOMMENDATIONS
    try:
        shared_memory = state_utils.get_shared_memory(vars)
        used_repeat_recommendation_phrases = shared_memory.get("used_repeat_recommendation_phrases", [])
        response = get_not_used_template(used_repeat_recommendation_phrases, REPEAT_RECOMMENDATION_PHRASES)
        state_utils.save_to_shared_memory(
            vars, used_repeat_recommendation_phrases=used_repeat_recommendation_phrases + [response]
        )

        movie_id_to_recommend = shared_memory.get("current_movie_id", "")
        response = fill_templates_with_movie_info(response, movie_id_to_recommend, genre=None)

        recom_offer = bot_offers_movie_recommendation_response(vars)

        state_utils.set_confidence(vars, HIGH_CONFIDENCE)
        state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)

        response = f"{response} {recom_offer}"
        return response

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


##################################################################################################################
# Interesting movie moment
##################################################################################################################


def share_movie_moment_response(vars):
    # USR_SHARE_INTERESTING_MOMENT
    try:
        shared_memory = state_utils.get_shared_memory(vars)
        used_interesting_moment_phrases = shared_memory.get("used_interesting_moment_phrases", [])
        movie_id = shared_memory.get("current_movie_id", "")
        plot = movieplots.get_plot(movie_id)
        plot_sentences = sent_tokenize(plot) if plot else []
        plot_sentences = plot_sentences[1:] if len(plot_sentences) > 1 else []

        if plot_sentences:
            response = get_not_used_template(used_interesting_moment_phrases, WHAT_IS_YOUR_FAVORITE_MOMENT_PHRASES)
            state_utils.save_to_shared_memory(
                vars, used_interesting_moment_phrases=used_interesting_moment_phrases + [response]
            )
            moment = find_first_complete_sentence(plot_sentences)
            state_utils.set_confidence(vars, HIGH_CONFIDENCE)
            state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
            return response.replace("MOMENT", moment)
        else:
            response = get_not_used_template(
                used_interesting_moment_phrases, WHAT_IS_YOUR_FAVORITE_MOMENT_NO_PLOT_FOUND_PHRASES
            )
            state_utils.save_to_shared_memory(
                vars, used_interesting_moment_phrases=used_interesting_moment_phrases + [response]
            )
            state_utils.set_confidence(vars, HIGH_CONFIDENCE)
            state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_SCENARIO)
            return response

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


##################################################################################################################
# continue talk about movies?
##################################################################################################################


def bot_asks_to_continue_movie_talk_response(vars):
    # USR_WAS_OFFERED_TO_CONTINUE_MOVIE_TALK
    try:
        shared_memory = state_utils.get_shared_memory(vars)
        used_continue_movie_talk_phrases = shared_memory.get("used_continue_movie_talk_phrases", [])
        response = get_not_used_template(used_continue_movie_talk_phrases, WOULD_YOU_LIKE_TO_CONTINUE_TALK_ABOUT_MOVIES)
        state_utils.save_to_shared_memory(
            vars, used_continue_movie_talk_phrases=used_continue_movie_talk_phrases + [response]
        )
        _user_was_asked_about_movie_title = user_was_asked_about_movie_title(vars)
        if _user_was_asked_about_movie_title and condition_utils.no_special_switch_off_requests(vars):
            state_utils.set_confidence(vars, SUPER_CONFIDENCE)
            state_utils.set_can_continue(vars, continue_flag=MUST_CONTINUE)
        else:
            state_utils.set_confidence(vars, HIGH_CONFIDENCE)
            state_utils.set_can_continue(vars, continue_flag=CAN_CONTINUE_PROMPT)

        if _user_was_asked_about_movie_title:
            response = f"{get_movie_template('dont_know_movie_title_at_all')} {response}"

        if recommendations_declined(vars):
            state_utils.save_to_shared_memory(vars, recommendations_declined=True)
        return response

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


def user_wants_to_continue_movie_talk_request(ngrams, vars):
    offer = any(
        [
            phrase in state_utils.get_last_bot_utterance(vars).get("text", "")
            for phrase in WOULD_YOU_LIKE_TO_CONTINUE_TALK_ABOUT_MOVIES
        ]
    )
    user_agrees = condition_utils.is_yes_vars(vars)

    if offer and user_agrees:
        logger.info(f"User wants to continue movie talk.")
        return True
    return False


##################################################################################################################
# error
##################################################################################################################


def error_response(vars):
    logger.info("exec error_response")
    state_utils.set_confidence(vars, ZERO_CONFIDENCE)
    state_utils.save_to_shared_memory(vars, current_status="")
    return "Sorry"


##################################################################################################################
##################################################################################################################
# linking
##################################################################################################################
##################################################################################################################


##################################################################################################################
#  START

simplified_dialogflow.add_user_serial_transitions(
    State.USR_START,
    {
        State.SYS_NOT_LIKE_MOVIES: user_not_like_movies_request,
        State.SYS_USER_REQUESTS_OPINION_ABOUT_MOVIE: opinion_requests_about_movie_request,
        State.SYS_EXTRACTED_MOVIE_TITLE: popular_movie_title_extracted_request,
        State.SYS_CLARIFY_MOVIE_TITLE: to_be_clarified_movie_title_extracted_request,
        State.SYS_USER_REQUESTS_OPINION_ABOUT_MOVIE_GENRE: opinion_requests_about_genre_request,
        State.SYS_USER_EXPRESSES_OPINION_ABOUT_MOVIE_GENRE: opinion_expression_about_movie_genres_request,
        State.SYS_USER_REQUESTS_MOVIE_RECOMMENDATION: recommendations_request,
        State.SYS_LETS_CHAT_ABOUT_MOVIES: lets_chat_about_movies_request,
        State.SYS_FAQ: faq_request,
        State.SYS_USR_WAS_ASKED_MOVIE_TITLE_QUESTION_AND_REFUSED: user_refused_movie_title_question_request,
        State.SYS_USR_WAS_ASKED_MOVIE_TITLE_QUESTION_NO_MOVIE_EXTRACTED_NO_RECOM: user_was_asked_about_movie_title_and_declined_recommendations_request,
        State.SYS_USR_WAS_ASKED_MOVIE_TITLE_QUESTION_NO_MOVIE_EXTRACTED: user_was_asked_about_movie_title_request,
        State.SYS_MENTIONED_MOVIES: mentioned_movies_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_START, State.SYS_ERR)

##################################################################################################################
#  SYS_FAQ

simplified_dialogflow.add_system_transition(State.SYS_FAQ, State.USR_FAQ, faq_response)

##################################################################################################################
#  SYS_USR_WAS_ASKED_MOVIE_TITLE_QUESTION_NO_MOVIE_EXTRACTED_NO_RECOM

simplified_dialogflow.add_system_transition(
    State.SYS_USR_WAS_ASKED_MOVIE_TITLE_QUESTION_NO_MOVIE_EXTRACTED_NO_RECOM,
    State.USR_WAS_OFFERED_TO_CONTINUE_MOVIE_TALK,
    bot_asks_to_continue_movie_talk_response,
)

##################################################################################################################
#  SYS_USR_WAS_ASKED_MOVIE_TITLE_QUESTION_NO_MOVIE_EXTRACTED

simplified_dialogflow.add_system_transition(
    State.SYS_USR_WAS_ASKED_MOVIE_TITLE_QUESTION_NO_MOVIE_EXTRACTED,
    State.USR_WAS_OFFERED_RECOMMENDATIONS,
    bot_offers_movie_recommendation_response,
)
##################################################################################################################
#  SYS_USR_WAS_ASKED_MOVIE_TITLE_QUESTION_AND_REFUSED

simplified_dialogflow.add_system_transition(
    State.SYS_USR_WAS_ASKED_MOVIE_TITLE_QUESTION_AND_REFUSED,
    State.USR_WAS_OFFERED_RECOMMENDATIONS,
    bot_offers_movie_recommendation_response,
)

##################################################################################################################
#  SYS_NOT_LIKE_MOVIES

simplified_dialogflow.add_system_transition(State.SYS_NOT_LIKE_MOVIES, State.USR_START, user_not_like_movies_response)

##################################################################################################################
#  SYS_USER_REQUESTS_MOVIE_RECOMMENDATION

simplified_dialogflow.add_system_transition(
    State.SYS_USER_REQUESTS_MOVIE_RECOMMENDATION, State.USR_ASKED_HAVE_SEEN_MOVIE, bot_recommends_movie_response
)

##################################################################################################################
#  USR_ASKED_HAVE_SEEN_MOVIE

simplified_dialogflow.add_user_serial_transitions(
    State.USR_ASKED_HAVE_SEEN_MOVIE,
    {
        State.SYS_EXTRACTED_MOVIE_TITLE: is_yes_request,
        State.SYS_REPEAT_RECOMMENDATION: is_no_request,
        State.SYS_MENTIONED_MOVIES: no_requests_request,  # not_confident_lets_chat_about_movies_response
    },
)
simplified_dialogflow.set_error_successor(State.USR_ASKED_HAVE_SEEN_MOVIE, State.SYS_ERR)


##################################################################################################################
#  SYS_REPEAT_RECOMMENDATION

simplified_dialogflow.add_system_transition(
    State.SYS_REPEAT_RECOMMENDATION,
    State.USR_WAS_OFFERED_RECOMMENDATIONS,
    bot_repeats_movie_recommends_and_offers_more_recomends_response,
)

##################################################################################################################
#  USR_ASKED_HAVE_SEEN_MOVIE

simplified_dialogflow.add_user_serial_transitions(
    State.USR_WAS_OFFERED_RECOMMENDATIONS,
    {
        State.SYS_OFFER_CONTINUE_MOVIE_TALK: is_no_request,  # user declined recommendations, offer continue movie talk
        State.SYS_USER_REQUESTS_MOVIE_RECOMMENDATION: no_requests_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_WAS_OFFERED_RECOMMENDATIONS, State.SYS_ERR)

##################################################################################################################
#  SYS_OFFER_CONTINUE_MOVIE_TALK

simplified_dialogflow.add_system_transition(
    State.SYS_OFFER_CONTINUE_MOVIE_TALK,
    State.USR_WAS_OFFERED_TO_CONTINUE_MOVIE_TALK,
    bot_asks_to_continue_movie_talk_response,
)

##################################################################################################################
#  USR_ASKED_HAVE_SEEN_MOVIE

simplified_dialogflow.add_user_serial_transitions(
    State.USR_WAS_OFFERED_TO_CONTINUE_MOVIE_TALK,
    {
        State.SYS_LETS_CHAT_ABOUT_MOVIES: is_yes_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_WAS_OFFERED_TO_CONTINUE_MOVIE_TALK, State.SYS_ERR)

##################################################################################################################
#  SYS_USER_EXPRESSES_OPINION_ABOUT_MOVIE_GENRE

simplified_dialogflow.add_system_transition(
    State.SYS_USER_EXPRESSES_OPINION_ABOUT_MOVIE_GENRE,
    State.USR_WAS_ASKED_MOVIE_TITLE_QUESTION,
    opinion_expression_about_movie_genres_response,
)

##################################################################################################################
#  SYS_USER_REQUESTS_OPINION_ABOUT_MOVIE

simplified_dialogflow.add_system_transition(
    State.SYS_USER_REQUESTS_OPINION_ABOUT_MOVIE,
    State.USR_WAS_REQUESTED_MOVIE_OPINION,
    bot_express_opinion_and_ask_user_response,
)

##################################################################################################################
#  SYS_USER_REQUESTS_OPINION_ABOUT_MOVIE_GENRE

simplified_dialogflow.add_system_transition(
    State.SYS_USER_REQUESTS_OPINION_ABOUT_MOVIE_GENRE,
    State.USR_WAS_REQUESTED_MOVIE_OPINION,
    bot_express_opinion_about_genre_and_ask_user_response,
)

##################################################################################################################
#  SYS_LETS_CHAT_ABOUT_MOVIES

simplified_dialogflow.add_system_transition(
    State.SYS_LETS_CHAT_ABOUT_MOVIES, State.USR_WAS_ASKED_MOVIE_TITLE_QUESTION, lets_chat_about_movies_response
)

##################################################################################################################
#  SYS_MENTIONED_MOVIES

simplified_dialogflow.add_system_transition(
    State.SYS_MENTIONED_MOVIES, State.USR_WAS_ASKED_MOVIE_TITLE_QUESTION, not_confident_lets_chat_about_movies_response
)

##################################################################################################################
#  USR_WAS_ASKED_MOVIE_TITLE_QUESTION

simplified_dialogflow.add_user_serial_transitions(
    State.USR_WAS_ASKED_MOVIE_TITLE_QUESTION,
    {
        State.SYS_EXTRACTED_MOVIE_TITLE: popular_movie_title_extracted_request,
        State.SYS_CLARIFY_MOVIE_TITLE: to_be_clarified_movie_title_extracted_request,
        State.SYS_USR_WAS_ASKED_MOVIE_TITLE_QUESTION_AND_REFUSED: user_refused_movie_title_question_request,
        State.SYS_USR_WAS_ASKED_MOVIE_TITLE_QUESTION_NO_MOVIE_EXTRACTED_NO_RECOM: user_was_asked_about_movie_title_and_declined_recommendations_request,
        State.SYS_USR_WAS_ASKED_MOVIE_TITLE_QUESTION_NO_MOVIE_EXTRACTED: user_was_asked_about_movie_title_request,
        State.SYS_OFFER_CONTINUE_MOVIE_TALK: no_requests_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_WAS_ASKED_MOVIE_TITLE_QUESTION, State.SYS_ERR)

##################################################################################################################
#  SYS_EXTRACTED_MOVIE_TITLE

simplified_dialogflow.add_system_transition(
    State.SYS_EXTRACTED_MOVIE_TITLE, State.USR_WAS_REQUESTED_MOVIE_OPINION, movie_request_opinion_response
)

##################################################################################################################
#  SYS_CLARIFY_MOVIE_TITLE

simplified_dialogflow.add_system_transition(
    State.SYS_CLARIFY_MOVIE_TITLE, State.USR_WAS_ASKED_TO_CLARIFY_MOVIE_TITLE, movie_title_clarification_response
)

##################################################################################################################
#  USR_WAS_ASKED_TO_CLARIFY_MOVIE_TITLE

simplified_dialogflow.add_user_serial_transitions(
    State.USR_WAS_ASKED_TO_CLARIFY_MOVIE_TITLE,
    {
        State.SYS_EXTRACTED_MOVIE_TITLE: clarified_movie_title_confirmed_request,
        State.SYS_CLARIFY_MOVIE_TITLE: clarify_movie_title_again_request,
        State.SYS_NOT_EXTRACTED_AFTER_CLARIFICATION: did_not_extracted_movie_title_after_clarification_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_WAS_ASKED_TO_CLARIFY_MOVIE_TITLE, State.SYS_ERR)

##################################################################################################################
#  SYS_NOT_EXTRACTED_AFTER_CLARIFICATION

simplified_dialogflow.add_system_transition(
    State.SYS_NOT_EXTRACTED_AFTER_CLARIFICATION,
    State.USR_WAS_ASKED_MOVIE_TITLE_QUESTION,
    movie_title_clarification_response,
)

##################################################################################################################
#  USR_WAS_REQUESTED_MOVIE_OPINION

simplified_dialogflow.add_user_serial_transitions(
    State.USR_WAS_REQUESTED_MOVIE_OPINION,
    {
        State.SYS_USER_NOT_WATCH_MOVIE: not_watched_request,
        State.SYS_ASK_DO_YOU_KNOW_QUESTION: no_requests_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_WAS_REQUESTED_MOVIE_OPINION, State.SYS_ERR)

##################################################################################################################
#  SYS_USER_NOT_WATCH_MOVIE

simplified_dialogflow.add_system_transition(
    State.SYS_USER_NOT_WATCH_MOVIE,
    State.USR_WAS_ASKED_MOVIE_TITLE_QUESTION,
    ackn_not_watch_ask_for_another_movie_response,
)

##################################################################################################################
#  SYS_ASK_DO_YOU_KNOW_QUESTION

simplified_dialogflow.add_system_transition(
    State.SYS_ASK_DO_YOU_KNOW_QUESTION, State.USR_WAS_ASKED_DO_YOU_KNOW_QUESTION, ask_do_you_know_question_response
)

##################################################################################################################
#  USR_WAS_REQUESTED_MOVIE_OPINION

simplified_dialogflow.add_user_serial_transitions(
    State.USR_WAS_ASKED_DO_YOU_KNOW_QUESTION,
    {
        State.SYS_CHECK_ANSWER_TO_DO_YOU_KNOW: do_you_know_question_need_to_be_checked_request,
        State.SYS_GIVE_FACT_ABOUT_MOVIE: no_requests_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_WAS_ASKED_DO_YOU_KNOW_QUESTION, State.SYS_ERR)

##################################################################################################################
#  SYS_ASK_DO_YOU_KNOW_QUESTION

simplified_dialogflow.add_system_transition(
    State.SYS_CHECK_ANSWER_TO_DO_YOU_KNOW,
    State.USR_CHECK_ANSWER_TO_DO_YOU_KNOW,
    check_answer_to_do_you_know_question_response,
)

##################################################################################################################
#  USR_CHECK_ANSWER_TO_DO_YOU_KNOW

simplified_dialogflow.add_user_serial_transitions(
    State.USR_CHECK_ANSWER_TO_DO_YOU_KNOW,
    {
        State.SYS_GIVE_FACT_ABOUT_MOVIE: no_requests_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_CHECK_ANSWER_TO_DO_YOU_KNOW, State.SYS_ERR)

##################################################################################################################
#  SYS_GIVE_FACT_ABOUT_MOVIE

simplified_dialogflow.add_system_transition(
    State.SYS_GIVE_FACT_ABOUT_MOVIE, State.USR_HAVE_YOU_HEARD_FACT, generate_fact_from_cobotqa_response
)
# share fact if available, if no fact - offer recommendations

##################################################################################################################
#  USR_CHECK_ANSWER_TO_DO_YOU_KNOW

simplified_dialogflow.add_user_serial_transitions(
    State.USR_HAVE_YOU_HEARD_FACT,
    {
        State.SYS_USER_REQUESTS_MOVIE_RECOMMENDATION: recommendations_request,  # if not fact & offered recommendations
        State.SYS_OFFER_CONTINUE_MOVIE_TALK: recommendations_declined_request,  # offer continue movie talk
        State.SYS_GIVE_FACT_ABOUT_MOVIE: give_more_fact_request,
        State.USR_WAS_OFFERED_RECOMMENDATIONS: no_requests_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_HAVE_YOU_HEARD_FACT, State.SYS_ERR)

##################################################################################################################
#  SYS_ASK_QUESTION_ABOUT_MOVIE_TITLE

simplified_dialogflow.add_system_transition(
    State.SYS_ASK_QUESTION_ABOUT_MOVIE_TITLE,
    State.USR_WAS_ASKED_MOVIE_TITLE_QUESTION,
    not_confident_lets_chat_about_movies_response,
)

##################################################################################################################
#  SYS_ERR
simplified_dialogflow.add_system_transition(
    State.SYS_ERR,
    (scopes.MAIN, scopes.State.USR_ROOT),
    error_response,
)
dialogflow = simplified_dialogflow.get_dialogflow()
