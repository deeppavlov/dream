import re

# from .sentiment import get_sentiment


def rm_greets_after_begin(**kwargs):
    reply = kwargs["reply"]
    utterances_histories = kwargs["utterances_histories"]
    if len(utterances_histories) > 2:
        stop_words = ["hello", "hi", "hey"]
        splitted_reply = re.sub(r'[\?\.,\!\'"\)\]]*', "", reply.strip().lower()).strip().split(" ")
        for word in stop_words:
            if word in splitted_reply:
                return

    return reply


# def to_positive_sentiment(**kwargs):
#     get_sentiment
#     reply = kwargs["reply"]
#     history_sentiment = kwargs["history_sentiment"]
#     sentiment = get_sentiment(reply)
#     if sentiment[0] == "negative":
#         return

#     if history_sentiment == "negative" and sentiment[0] == "neutral" and sentiment[1] != 1:
#         return

#     return reply


heuristics_pipline = [rm_greets_after_begin]


def apply_heuristics(**kwargs):
    for func in heuristics_pipline:
        reply = func(**kwargs)
        if reply is None:
            return
        kwargs["reply"] = func(**kwargs)
    reply = kwargs.get("reply", "")
    return reply
