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
    regexp = {
        intent: re.compile(join_sentences_in_or_pattern(phrases), re.IGNORECASE) for intent, phrases in regexp.items()
    }
    return regexp


def join_sentences_in_or_pattern(sents):
    return r"(" + r"|".join(sents) + r")"


INTENT_PHRASES_PATH = (
    "/home/petryashin_ie/deeppavlov_tasks/dream/annotators/IntentCatcherTransformers/robot_intent_phrases.json"
)

regexp = get_regexp(INTENT_PHRASES_PATH)

print("Success")
