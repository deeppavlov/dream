import logging
from os import getenv

import common.dff.integration.context as int_ctx
import common.dialogflow_framework.utils.state as state_utils
import common.utils as common_utils
import requests
from common.dff.integration import condition as int_cnd
from common.universal_templates import (COMPILE_NOT_WANT_TO_TALK_ABOUT_IT,
                                        is_any_question_sentence_in_utterance,
                                        is_what_question_in_utterance)
import re
from df_engine.core import Actor, Context

logger = logging.getLogger(__name__)

WHAT_IS_QUESTION = re.compile(r'what is|what does .* mean|what\?|what do you mean|what are|^what$', re.IGNORECASE)
THANK_PATTERN = re.compile(r"thanks|thank you|(I'll|I will) (try|watch|read|cook|think)", re.IGNORECASE)


def have_questions_left(ctx: Context, actor: Actor, *args, **kwargs):
    if ctx.misc.get("slots", {}).get("time_to_go", False):
        return False
    else:
        return True

    
def contains_noun_phrase(ctx: Context, actor: Actor, *args, **kwargs):
        result = int_ctx.get_nounphrases_from_human_utterance(ctx, actor)
        if result:
            return True
        else:
            return False


def contains_named_entities(ctx: Context, actor: Actor, *args, **kwargs):
        result = int_ctx.get_named_entities_from_human_utterance(ctx, actor)
        logger.info(f"get_named_entities_from_human_utterance -- {result}")
        if result:
            if result[0]['type'] != 'CARDINAL':
                return True
            else: 
                return False
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
    shared_memory = int_ctx.get_shared_memory(ctx, actor)
    num_gen_responses = int(shared_memory.get("num_gen_responses", 0))
    if num_gen_responses > 1: 
        logger.info(f"enough_generative_responses -- too much generative responses: {num_gen_responses}")
        return True
    else:
        logger.info(f"enough_generative_responses -- norm generative responses: {num_gen_responses}")
        return False


def bot_takes_initiative(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    human_uttrs = int_ctx.get_human_utterances(ctx, actor)
    if int_cnd.no_requests and int_cnd.is_passive_user and len(human_uttrs) > 1:
        return True
    else:
        return False


def is_hyponym(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    return bool(ctx.misc.get("slots", {}).get('we_found_hyp', False))


def what_is_question(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    if ctx.validation:
        return False
    text = int_ctx.get_last_human_utterance(ctx, actor)["text"]
    is_question_any_sent = re.search(WHAT_IS_QUESTION, text)
    return bool(is_question_any_sent)


def we_have_hyp_def(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    return bool(ctx.misc.get("slots", {}).get('current_hyp_definition', False))


def hyp_question_asked(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    if ctx.misc.get("slots", {}).get('hyp_question_asked', False):
        ctx.misc['slots']['hyp_question_asked'] = False
        return True
    # elif 'hyp_question_asked' not in ctx.misc.get("slots", {}):
    #     return True
    else:
        return False


def short_thank_you(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    if ctx.validation:
        return False
    text = int_ctx.get_last_human_utterance(ctx, actor)["text"]
    if re.search(THANK_PATTERN, text) and len(text.split(' ')) < 4:
        return True
    else:
        return False