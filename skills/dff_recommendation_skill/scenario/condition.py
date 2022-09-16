import logging

from df_engine.core import Context, Actor

from common.dff.integration import condition as int_cnd
import common.dff.integration.context as int_ctx
import common.dialogflow_framework.utils.state as state_utils
import common.utils as common_utils

logger = logging.getLogger(__name__)
# ....


def example_lets_talk_about():
    def example_lets_talk_about_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        return int_cnd.is_lets_chat_about_topic_human_initiative(ctx, actor)

    return example_lets_talk_about_handler


# def give_last_human_utt(ctx: Context, actor: Actor, *args, **kwargs) -> str:
#     human_text = int_ctx.get_last_human_utterance(ctx, actor)["text"]
#     return human_text

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


def is_positive_sentiment():
    def is_positive_sentiment_handler(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
        sentiment = state_utils.get_human_sentiment(ctx)
        print(sentiment)
        if sentiment == 'positive':
            return True
        else: 
            return False

    return is_positive_sentiment_handler


def is_negative_sentiment(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    if ctx.misc:
        sentiment = state_utils.get_human_sentiment(ctx.misc["agent"]["dialog"]["human_utterances"][-1])
        if sentiment == 'negative':
            return True
        else: 
            return False
    return False

