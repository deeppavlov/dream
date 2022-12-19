import json
import re
from itertools import chain
from typing import List

from common.universal_templates import join_sentences_in_or_pattern


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


def unite_responses(responses_a: List[dict], responses_b: List[dict], all_intents_to_consider):
    assert len(responses_a) == len(responses_b)
    result = []
    for a, b in zip(responses_a, responses_b):
        resp = {}
        for intent in all_intents_to_consider:
            a_intent = a.get(intent, {"detected": 0, "confidence": 0.0})
            b_intent = b.get(intent, {"detected": 0, "confidence": 0.0})
            resp[intent] = {
                "detected": max(a_intent["detected"], b_intent["detected"]),
                "confidence": max(a_intent["confidence"], b_intent["confidence"]),
            }
        result.append(resp)
    return result
