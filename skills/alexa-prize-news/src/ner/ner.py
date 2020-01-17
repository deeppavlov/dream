from collections import defaultdict

from deeppavlov import configs, build_model
from deeppavlov.utils.pip_wrapper import install_from_config


ner = None


def get_ner():
    global ner
    if ner is not None:
        return ner
    else:
        model_config = configs.ner.ner_conll2003_bert
        install_from_config(model_config)
        ner = build_model(model_config, download=True)
        return ner


def get_ner_index(texts):
    # get_ner()  # init ner
    tags = ["organization", "person", "location"]
    indices = [get_ner_index_for_tag(texts, key) for key in tags]
    index = defaultdict(list)
    for i in indices:
        for k, v in i.items():
            index[k].extend(v)
    return index


def get_ner_index_for_tag(texts, tag):
    index = defaultdict(list)
    for i, text in enumerate(texts):
        if tag in text:
            for entity in text[tag]:
                index[entity.lower()].append(i)
    return index


def find_any_tag(message, tags):
    """
    Returns the first found entity, corresponding to `tags`.
    :param message: message to find entities from
    :param tags: requested tags
    :return: a phrase corresponding to some tag in the `tags` list, or None
    """
    predictions = get_ner()([message])
    predictions = reduce(predictions)
    result = first_match(predictions, tags)
    return result


def reduce(predictions):
    """
    Takes NER model output and joins the word-tag pairs into phrase-tag pairs.
    :param predictions: prediction in the NER output format
    :return: a list of phrase-tag pairs
    """
    words, predictions = predictions[0][0], predictions[1][0]
    result = []
    w_last, p_last = "", ""

    for w, p in zip(words, predictions):
        if "I-" in p and result and p[2:] == p_last:
            result[-1] = w_last + " " + w, p_last
        elif "I-" in p or "B-" in p:
            result.append((w, p[2:]))

        if result:
            w_last, p_last = result[-1]

    return result


def first_match(predictions, tags):
    """
    First match for the requested `tags`.
    :param predictions: a list of phrase-tag pairs
    :param tags: a list of requested tags
    :return: a first phrase (or None), corresponding to some tag in the `tags` list
    """
    tag2words = defaultdict(list)
    for w, t in reversed(predictions):
        tag2words[t].append(w)

    for t in tags:
        if t in tag2words and tag2words[t]:
            return tag2words[t].pop()

    return None
