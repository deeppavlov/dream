import logging

from nltk.stem import WordNetLemmatizer

from dff.core import Context, Actor

import common.utils as common_utils

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

wnl = WordNetLemmatizer()


#  vars is described in README.md


def was_clarification_request(ctx: Context, actor: Actor):
    flag = ctx.misc["agent"]["clarification_request_flag"]
    logging.debug(f"was_clarification_request = {flag}")
    return flag


def is_opinion_request(ctx: Context, actor: Actor):
    flag = common_utils.is_opinion_request(ctx.misc["agent"]["dialog"]["human_utterances"][-1])
    logging.debug(f"is_opinion_request = {flag}")
    return flag


def is_opinion_expression(ctx: Context, actor: Actor):
    flag = common_utils.is_opinion_expression(ctx.misc["agent"]["dialog"]["human_utterances"][-1])
    logging.debug(f"is_opinion_expression = {flag}")
    return flag
