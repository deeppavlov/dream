#!/usr/bin/env python

import logging
import time
import re
import random
import collections
import itertools

from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk


sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    last_utter_batch = request.json["sentences"]
    responses = []

    for last_utter in last_utter_batch:
        response_text, confidence = dialog_segment_handler(last_utter)
        logger.info(f"Last_utter = {last_utter}")
        logger.info(f"Response_text = {response_text}")

        responses.append((response_text, confidence))

    total_time = time.time() - st_time
    logger.info(f"valentines day exec time = {total_time:.3f}s")
    return jsonify(responses)


ANY_PATTERN = r"(['a-zA-z ]+)?"


def add_ANY_PATTERN(ordered_key_regs):
    regs = ANY_PATTERN.join(ordered_key_regs)
    return regs


def and_merge_regs(regs):
    regs = [and_merge_regs(reg) for reg in regs] if isinstance(regs[0], (list, tuple)) else regs
    assert isinstance(regs[0], str)
    if len(regs) > 1:
        return ".*".join([f"({reg})" for reg in regs])
    elif len(regs) == 1:
        return regs[0]
    raise "Unallowed segment regs"


def or_merge_regs(regs):
    regs = [or_merge_regs(reg) for reg in regs] if isinstance(regs[0], (list, tuple)) else regs
    assert isinstance(regs[0], str)
    if len(regs) > 1:
        return "|".join([f"({reg})" for reg in regs])
    elif len(regs) == 1:
        return regs[0]
    raise "Unallowed segment regs"


def compile_regs(dictionary):
    for key in dictionary.keys():
        # logger.info(f"key = {key}, dictionary[key] = {dictionary[key]}")
        dictionary[key] = re.compile(dictionary[key])
    return dictionary


# bag-of-words
def create_bow(regs, add_any_pattern=True):
    regs = itertools.permutations(regs, len(regs))
    regs = [and_merge_regs(reg) for reg in regs] if add_any_pattern else regs
    return or_merge_regs(list(regs))


dialog_segment_regs = collections.OrderedDict()
dialog_segment_candidates = collections.OrderedDict()
#  ordered by priority


def template_regs(filling_data: dict):
    regs = {}
    for k, v in filling_data.items():
        adds = v.get("adds", [r"(valentin)"])
        regs[k] = (
            or_merge_regs([create_bow(adds + _reg) for _reg in v["regs"]])
            if adds
            else or_merge_regs([create_bow(_reg) for _reg in v["regs"]])
        )
        if v.get("aggressive"):
            regs[f"aggressive_{k}"] = or_merge_regs([create_bow(_reg) for _reg in v["regs"]])
    return regs


def template_cands(filling_data: dict):
    cands = {}
    for k, v in filling_data.items():
        cands[k] = v["candidates"]
        cands[f"aggressive_{k}"] = v["candidates"]
    return cands


valentines = collections.OrderedDict()
valentines["what_is_love"] = {
    "candidates": ["Baby don't hurt me. Don't hurt me. No more"],
    "aggressive": True,
    "regs": [[r"what is love"]],
    "adds": [],
}
valentines["about_love"] = {
    "candidates": [
        "Love takes off masks that we fear we cannot live without and know we cannot live within."
        " Quote by James Baldwin",
        "Love is a friendship set to music. Quote by Joseph Campbell",
        "We are shaped and fashioned by what we love. Quote by Johann Wolfgang von Goethe",
        "Love in its essence is spiritual fire. Quote by Senecae",
    ],
    "aggressive": True,
    "regs": [
        [r"what.*is.*lov(e|ing).*"],
        [r"(fact|anything|something|talk|chat|say|speak|tell).*about.*lov(e|ing)"],
        [r"(do|are).*know.*lov(e|ing)"],
    ],
    "adds": [],
}
valentines["who_you_love"] = {
    "candidates": [
        "This is a big secret, I can say that he is strong man.",
        "This is a big secret, I can say that he is good man.",
        "This is a big secret, I can say that he is clever man.",
        "This is a big secret, I can say that he is cute man.",
    ],
    "aggressive": True,
    "regs": [[r"who.*(do|are).*you.*lov(e|ing).*"]],
    "adds": [],
}
valentines["do_you_love"] = {
    "candidates": ["Yes, I love, but it's a big big secret, I won’t tell anyone about it", "Yes love is beautiful"],
    "aggressive": True,
    "regs": [[r"(do|are).*you.*lov(e|ing).*"]],
    "adds": [],
}
valentines["received_card"] = {
    "candidates": [
        "Yes, I received the the Valentine's Day card by email. But it's a secret",
    ],
    "aggressive": True,
    "regs": [[r"(do|did).*you.*(get|gain|grab|have|obtain|receive).*valentin.*"]],
    "adds": [],
}
valentines["valentines_day"] = {
    "candidates": [
        "Valentine's Day is a wonderful day, every time I look forward to it",
    ],
    "aggressive": True,
    "regs": [
        [r"what.*is.*valentine.*day"],
        [r"(anything|something|talk|chat|say|speak|tell).*about.*valentine.*day"],
        [r"do .*know.*valentine.*day"],
    ],
    "adds": [],
}

dialog_segment_regs.update(template_regs(valentines))
dialog_segment_candidates.update(template_cands(valentines))

dialog_segment_regs = compile_regs(dialog_segment_regs)


def dialog_segment_handler(last_utter):
    response = ""
    confidence = 0.0
    curr_user_uttr = last_utter.lower()

    active_segments = [
        segment_name for segment_name, segment_reg in dialog_segment_regs.items() if segment_reg.search(curr_user_uttr)
    ]
    logger.info(f"active_segments = {active_segments}")
    if active_segments:
        response = random.choice(dialog_segment_candidates[active_segments[0]])
        confidence = 0.99 if len(active_segments) > 1 else 0.8
    return response, confidence


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
