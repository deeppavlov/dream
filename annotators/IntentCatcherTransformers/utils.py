import json
import re
from itertools import chain


def get_regexp(intent_phrases_path):
    regexp = {
        intent: list(
            chain.from_iterable(
                [[phrase + "\\" + punct for phrase in data["phrases"]] for punct in data["punctuation"]]
            )
        )
        + [rf"^{pattern}[\.\?!]?$" for pattern in data.get("reg_phrases", [])]
        for intent, data in json.load(open(intent_phrases_path))["intent_phrases"].items()
    }
    regexp = {intent: [re.compile(phrase) for phrase in phrases] for intent, phrases in regexp.items()}
    return regexp
