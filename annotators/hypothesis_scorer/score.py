import midas
import convert
from catboost import CatBoostClassifier
import numpy as np

cb = CatBoostClassifier()
cb.load_model("model.cbm")


def get_convert_features(dialogues):
    features = []
    for dialogue in dialogues:
        context = dialogue["context"]
        responses = [x["text"] for x in dialogue["hyp"]]
        res = convert.get_convert_score(context, responses)
        features.append(res.reshape(-1, 1))
    return np.vstack(features)


def get_midas_features_human(dialogues):
    requests = []
    for dialogue in dialogues:
        context = dialogue["context"]
        last_human = context[-1]
        last_bot = context[-2] if len(context) > 1 else ""
        item = last_bot + " : EMPTY > " + last_human
        requests.append(item)

    res = midas.predict(requests)
    res = [list(x.values()) for x in res]
    return res


def get_midas_features_bot(dialogues):
    requests = []
    for dialogue in dialogues:
        context = dialogue["context"]
        last_human = context[-1]
        for hyp in dialogue["hyp"]:
            cur_bot = hyp["text"]
            item = last_human + " : EMPTY > " + cur_bot
            requests.append(item)
    res = midas.predict(requests)
    res = [list(x.values()) for x in res]
    return res


def get_midas_features(dialogues):
    midas_features_bot = get_midas_features_bot(dialogues)
    midas_features_human = get_midas_features_human(dialogues)
    item_idx = 0
    res = []
    for d_idx, h_features in enumerate(midas_features_human):
        for _ in range(len(dialogues[d_idx]["hyp"])):
            b_features = midas_features_bot[item_idx]
            item_idx += 1
            res.append(np.r_[b_features, h_features])

    assert item_idx == len(midas_features_bot)
    return np.stack(res)


def get_confidence(dialogues):
    res = []
    for dialogue in dialogues:
        for hyp in dialogue["hyp"]:
            res.append(hyp["confidence"])
    return np.array(res).reshape(-1, 1)


def get_cobot_anno(dialogues):
    res = []
    for dialogue in dialogues:
        for hyp in dialogue["hyp"]:
            anno = list(hyp["cobot_convers_evaluator_annotator"].values())
            res.append(np.array(anno))
    return np.stack(res)


def get_features(dialogues):
    X_conf = get_confidence(dialogues)
    X_cobot = get_cobot_anno(dialogues)
    X_conv = get_convert_features(dialogues)
    X_midas = get_midas_features(dialogues)
    return np.concatenate([X_conf, X_cobot, X_conv, X_midas], axis=1)


def get_probas(dialogues):
    features = get_features(dialogues)
    pred = cb.predict_proba(features)[:, 1]
    return pred


def get_final_answer(dialogues, pred):
    res = []
    item_idx = 0
    for dialogue in dialogues:
        cur_res = []
        for _ in range(len(dialogue["hyp"])):
            cur_res.append(pred[item_idx])
            item_idx += 1
        res.append(cur_res)
    assert item_idx == len(pred)
    return res


def predict(dialogues):
    pred = get_probas(dialogues)
    ans = get_final_answer(dialogues, pred)
    return ans
