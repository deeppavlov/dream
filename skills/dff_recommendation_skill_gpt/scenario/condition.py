import logging
from os import getenv

import common.dff.integration.context as int_ctx
import common.dialogflow_framework.utils.state as state_utils
import common.utils as common_utils
import requests
from common.dff.integration import condition as int_cnd
from common.universal_templates import (COMPILE_NOT_WANT_TO_TALK_ABOUT_IT,
                                        is_any_question_sentence_in_utterance)
from df_engine.core import Actor, Context

logger = logging.getLogger(__name__)


def contains_noun_phrase(ctx: Context, actor: Actor, *args, **kwargs):
        result = int_ctx.get_nounphrases_from_human_utterance(ctx, actor)
        if result:
            return True
        else:
            return False


def contains_named_entities(ctx: Context, actor: Actor, *args, **kwargs):
        result = int_ctx.get_named_entities_from_human_utterance(ctx, actor)
        if result:
            return True
        else:
            return False


def is_slot_filled(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    if ctx.misc.get("slots", []):
        if ctx.misc["slots"]["first_discussed_entity"]:
            return True
        else: 
            return False
    else:
        return False


def is_question(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    user_uttr = state_utils.get_last_human_utterance(ctx, actor)
    return is_any_question_sentence_in_utterance(user_uttr)


def get_human_sentiment(annotated_utterance, negative_threshold=0.5, positive_threshold=0.333):
    sentiment_probs = common_utils.get_sentiment(annotated_utterance, probs=True)
    if sentiment_probs and isinstance(sentiment_probs, dict):
        max_sentiment_prob = max(sentiment_probs.values())
        max_sentiments = [
            sentiment for sentiment in sentiment_probs if sentiment_probs[sentiment] == max_sentiment_prob
        ]
        if max_sentiments:
            max_sentiment = max_sentiments[0]
            return_negative = max_sentiment == "negative" and max_sentiment_prob >= negative_threshold
            return_positive = max_sentiment == "positive" and max_sentiment_prob >= positive_threshold
            if return_negative or return_positive:
                return max_sentiment
    return "neutral"


def is_positive_sentiment(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    if ctx.misc:
        sentiment = state_utils.get_human_sentiment(ctx.misc)
        if sentiment == 'positive':
            return True
        else: 
            return False
    else:
        return False


def is_negative_sentiment(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    if ctx.validation:
        return False
    if ctx.misc:
        sentiment = state_utils.get_human_sentiment(ctx.misc)
        if sentiment == 'negative':
            return True
        else: 
            return False
    else:
        return False


def enough_generative_responses(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    if int(ctx.misc.get("num_gen_responses", 0)) > 3: 
        ctx.misc["slots"]["num_gen_responses"] = 0
        return True
    else:
        return False


def bot_takes_initiative(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    human_uttrs = int_ctx.get_human_utterances(ctx, actor)
    if int_cnd.is_passive_user and int_cnd.no_requests and len(human_uttrs) > 2:
        return True
    else:
        return False