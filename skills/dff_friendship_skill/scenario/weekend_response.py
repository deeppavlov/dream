import logging
import random
import sentry_sdk
from os import getenv
from typing import Tuple

import common.dff.integration.condition as int_cnd
import common.dff.integration.context as int_ctx
import common.greeting as common_greeting
import common.scenarios.weekend as common_weekend
from common.constants import CAN_CONTINUE_SCENARIO
from df_engine.core import Actor, Context


sentry_sdk.init(getenv("SENTRY_DSN"))
logger = logging.getLogger(__name__)

LANGUAGE = getenv("LANGUAGE", "EN")

REPLY_TYPE = Tuple[str, float, dict, dict, dict]
DIALOG_BEGINNING_START_CONFIDENCE = 0.98
DIALOG_BEGINNING_CONTINUE_CONFIDENCE = 0.9
DIALOG_BEGINNING_SHORT_ANSWER_CONFIDENCE = 0.98
MIDDLE_DIALOG_START_CONFIDENCE = 0.7
SUPER_CONFIDENCE = 0.98
HIGH_CONFIDENCE = 0.95
MIDDLE_CONFIDENCE = 0.92
GREETING_STEPS = list(common_greeting.GREETING_QUESTIONS[LANGUAGE])


def std_weekend_response(ctx: Context, actor: Actor) -> str:
    # get ack, body
    ack = int_cnd.get_not_used_and_save_sentiment_acknowledgement(ctx, actor, lang=LANGUAGE)

    # obtaining random response from weekend questions
    body = random.choice(common_weekend.WEEKEND_QUESTIONS)

    # set confidence
    int_ctx.set_confidence(ctx, actor, DIALOG_BEGINNING_START_CONFIDENCE)
    int_ctx.set_can_continue(ctx, actor, CAN_CONTINUE_SCENARIO)
    int_ctx.add_acknowledgement_to_response_parts(ctx, actor)

    return " ".join([ack, body])


def sys_cleaned_up_response(ctx: Context, actor: Actor) -> str:
    # get ack, body
    ack = int_cnd.get_not_used_and_save_sentiment_acknowledgement(ctx, actor, lang=LANGUAGE)

    # obtaining random response from weekend questions
    body = random.choice(common_weekend.CLEANED_UP_STATEMENTS)

    # set confidence
    int_ctx.set_confidence(ctx, actor, DIALOG_BEGINNING_CONTINUE_CONFIDENCE)
    int_ctx.set_can_continue(ctx, actor, CAN_CONTINUE_SCENARIO)
    int_ctx.add_acknowledgement_to_response_parts(ctx, actor)

    return " ".join([ack, body])


def sys_slept_in_response(ctx: Context, actor: Actor) -> str:
    # get ack, body
    ack = int_cnd.get_not_used_and_save_sentiment_acknowledgement(ctx, actor, lang=LANGUAGE)

    # obtaining random response from weekend questions
    body = random.choice(common_weekend.SLEPT_IN_QUESTIONS)

    # set confidence
    int_ctx.set_confidence(ctx, actor, DIALOG_BEGINNING_START_CONFIDENCE)
    int_ctx.set_can_continue(ctx, actor, CAN_CONTINUE_SCENARIO)
    int_ctx.add_acknowledgement_to_response_parts(ctx, actor)

    return " ".join([ack, body])


def sys_feel_great_response(ctx: Context, actor: Actor) -> str:
    # get ack, body
    ack = int_cnd.get_not_used_and_save_sentiment_acknowledgement(ctx, actor, lang=LANGUAGE)

    # obtaining random response from weekend questions
    body = random.choice(common_weekend.WHAT_PLANS_FOR_TODAY)

    # set confidence
    int_ctx.set_confidence(ctx, actor, DIALOG_BEGINNING_CONTINUE_CONFIDENCE)
    int_ctx.set_can_continue(ctx, actor, CAN_CONTINUE_SCENARIO)
    int_ctx.add_acknowledgement_to_response_parts(ctx, actor)

    return " ".join([ack, body])


def sys_need_more_time_response(ctx: Context, actor: Actor) -> str:
    # get ack, body
    ack = int_cnd.get_not_used_and_save_sentiment_acknowledgement(ctx, actor, lang=LANGUAGE)

    # obtaining random response from weekend questions
    body = random.choice(common_weekend.WISH_MORE_TIME)

    # set confidence
    int_ctx.set_confidence(ctx, actor, DIALOG_BEGINNING_CONTINUE_CONFIDENCE)
    int_ctx.set_can_continue(ctx, actor, CAN_CONTINUE_SCENARIO)
    int_ctx.add_acknowledgement_to_response_parts(ctx, actor)

    return " ".join([ack, body])


def sys_watched_film_response(ctx: Context, actor: Actor) -> str:
    # get ack, body
    ack = int_cnd.get_not_used_and_save_sentiment_acknowledgement(ctx, actor, lang=LANGUAGE)

    # obtaining random response from weekend questions
    body = random.choice(common_weekend.MOVIE_NAME_QUESTION)

    # set confidence
    int_ctx.set_confidence(ctx, actor, DIALOG_BEGINNING_CONTINUE_CONFIDENCE)
    int_ctx.set_can_continue(ctx, actor, CAN_CONTINUE_SCENARIO)
    int_ctx.add_acknowledgement_to_response_parts(ctx, actor)

    return " ".join([ack, body])


def sys_read_book_response(ctx: Context, actor: Actor) -> str:
    # get ack, body
    ack = int_cnd.get_not_used_and_save_sentiment_acknowledgement(ctx, actor, lang=LANGUAGE)

    # obtaining random response from weekend questions
    body = random.choice(common_weekend.BOOK_NAME_QUESTION)

    # set confidence
    int_ctx.set_confidence(ctx, actor, DIALOG_BEGINNING_CONTINUE_CONFIDENCE)
    int_ctx.set_can_continue(ctx, actor, CAN_CONTINUE_SCENARIO)
    int_ctx.add_acknowledgement_to_response_parts(ctx, actor)

    return " ".join([ack, body])


def sys_played_computer_game_response(ctx: Context, actor: Actor) -> str:
    # get ack, body
    ack = int_cnd.get_not_used_and_save_sentiment_acknowledgement(ctx, actor, lang=LANGUAGE)

    # obtaining random response from weekend questions
    body = random.choice(common_weekend.COMPUTER_GAME_NAME_QUESTION)

    # set confidence
    int_ctx.set_confidence(ctx, actor, DIALOG_BEGINNING_CONTINUE_CONFIDENCE)
    int_ctx.set_can_continue(ctx, actor, CAN_CONTINUE_SCENARIO)
    int_ctx.add_acknowledgement_to_response_parts(ctx, actor)

    return " ".join([ack, body])


def sys_play_on_weekends_response(ctx: Context, actor: Actor) -> str:
    # get ack, body
    ack = int_cnd.get_not_used_and_save_sentiment_acknowledgement(ctx, actor, lang=LANGUAGE)

    # obtaining random response from weekend questions
    body = random.choice(common_weekend.GAME_EMOTIONS_QUESTION)

    # set confidence
    int_ctx.set_confidence(ctx, actor, DIALOG_BEGINNING_CONTINUE_CONFIDENCE)
    int_ctx.set_can_continue(ctx, actor, CAN_CONTINUE_SCENARIO)
    int_ctx.add_acknowledgement_to_response_parts(ctx, actor)

    return " ".join([ack, body])


def sys_play_regularly_response(ctx: Context, actor: Actor) -> str:
    # get ack, body
    ack = int_cnd.get_not_used_and_save_sentiment_acknowledgement(ctx, actor, lang=LANGUAGE)

    # obtaining random response from weekend questions
    body = random.choice(common_weekend.REGULAR_PLAYER_QUESTION)

    # set confidence
    int_ctx.set_confidence(ctx, actor, DIALOG_BEGINNING_CONTINUE_CONFIDENCE)
    int_ctx.set_can_continue(ctx, actor, CAN_CONTINUE_SCENARIO)
    int_ctx.add_acknowledgement_to_response_parts(ctx, actor)

    return " ".join([ack, body])


def sys_play_once_response(ctx: Context, actor: Actor) -> str:
    # get ack, body
    ack = int_cnd.get_not_used_and_save_sentiment_acknowledgement(ctx, actor, lang=LANGUAGE)

    # obtaining random response from weekend questions
    body = random.choice(common_weekend.OCCASIONAL_PLAYER_QUESTION)

    # set confidence
    int_ctx.set_confidence(ctx, actor, DIALOG_BEGINNING_CONTINUE_CONFIDENCE)
    int_ctx.set_can_continue(ctx, actor, CAN_CONTINUE_SCENARIO)
    int_ctx.add_acknowledgement_to_response_parts(ctx, actor)

    return " ".join([ack, body])
