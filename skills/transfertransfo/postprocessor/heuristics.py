import re


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


heuristics_pipline = [rm_greets_after_begin]


def apply_heuristics(**kwargs):
    for func in heuristics_pipline:
        reply = func(**kwargs)
        if reply is None:
            return
        kwargs["reply"] = func(**kwargs)
    reply = kwargs.get("reply", "")
    return reply
