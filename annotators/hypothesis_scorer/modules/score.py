from . import midas
from . import convert
import numpy as np


def get_midas_features_human(contexts):
    requests = []
    for context in contexts:
        last_human = context[-1]
        last_bot = context[-2] if len(context) > 1 else ""
        item = last_bot + " : EMPTY > " + last_human
        requests.append(item)

    return [list(x.values()) for x in midas.predict(requests)]


def get_midas_features_bot(contexts, hypotheses):
    requests = []
    for context, hyp in zip(contexts, hypotheses):
        last_human = context[-1]
        cur_bot = hyp["text"]
        item = last_human + " : EMPTY > " + cur_bot
        requests.append(item)

    return [list(x.values()) for x in midas.predict(requests)]


def get_features(contexts, hypotheses):
    X_conf = np.array([hyp["confidence"] for hyp in hypotheses]).reshape(-1, 1)

    X_conv = convert.get_convert_score(contexts, [hyp["text"] for hyp in hypotheses])

    midas_features_bot = get_midas_features_bot(contexts, hypotheses)
    midas_features_human = get_midas_features_human(contexts)
    X_midas = np.hstack([midas_features_bot, midas_features_human])

    return np.concatenate([X_conf, X_conv, X_midas], axis=1)
