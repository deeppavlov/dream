#!/usr/bin/env python

import logging
import time
import re
import random
import json
import collections

from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk


sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

fun_facts = json.load(open("./content/fun_facts.json"))
forty_niner_fun_facts = json.load(open("./content/49_fun_facts.json"))
chiefs_fun_facts = json.load(open("./content/chiefs_fun_facts.json"))


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    last_utter_batch = request.json["sentences"]
    responses = []

    for last_utter in last_utter_batch:
        response_text, confidence = dialog_segment_handler(last_utter)
        logger.info(f"Last_utter: {last_utter}")
        logger.info(f"Response_text: {response_text}")

        responses.append((response_text, confidence))

    total_time = time.time() - st_time
    logger.info(f"super bowl skill exec time: {total_time:.3f}s")
    return jsonify(responses)


ANY_PATTERN = r"(['a-zA-z ]+)?"


def add_ANY_PATTERN(ordered_key_regs):
    regs = ANY_PATTERN.join(ordered_key_regs)
    return regs


def merge_regs(regs):
    return "|".join([f"({reg})" for reg in regs])


def compile_regs(dictionary):
    for key in dictionary.keys():
        dictionary[key] = re.compile(dictionary[key])
    return dictionary


dialog_segment_regs = collections.OrderedDict()
#  ordered by priority
# dialog_segment_regs["who_wins"] = add_ANY_PATTERN([r"(who|which)", r"(win|make|won)", "super", r"bowls?(\s|$)"])
# dialog_segment_regs["who_goes"] = add_ANY_PATTERN(
#     [r"(who)", r"(going|gonna|play|will be in)", r"^(win|make)", "super", r"bowls?(\s|$)"]
# )
# dialog_segment_regs["what_time"] = add_ANY_PATTERN([r"(what)", r"(time)", "super", r"bowls?(\s|$)"])
dialog_segment_regs["fun_facts"] = add_ANY_PATTERN([r"(fact|anything|something)", r"about", "super", r"bowls?(\s|$)"])
dialog_segment_regs["talk_about"] = add_ANY_PATTERN([r"(talk|chat|say|speak|tell)", r"about", "super", r"bowls?(\s|$)"])
dialog_segment_regs["forty_niner"] = merge_regs(
    [
        add_ANY_PATTERN([r"forty niner", "super", r"bowls?(\s|$)"]),
        add_ANY_PATTERN([r"super", r"bowls?\s", "forty niner"]),
    ]
)
dialog_segment_regs["chiefs"] = merge_regs(
    [add_ANY_PATTERN([r"chief", "super", r"bowls?(\s|$)"]), add_ANY_PATTERN([r"super", r"bowls?\s", "chief"])]
)
dialog_segment_regs["what_about"] = add_ANY_PATTERN([r"what about (the )?super bowls?(\s|$)"])
dialog_segment_regs["super_bowl"] = add_ANY_PATTERN([r"(the )?super bowls?(\s|$)"])

faq_candidetes = {
    # "who_wins": ["The wait for the Kansas City Chiefs -- and for their head coach -- is finally over."
    #              "A half century after winning their first Super Bowl, the Chiefs are champions once more,"
    #              "winning Super Bowl LIV in epic fashion at Hard Rock Stadium."],
    # "who_goes": ["The Kansas City Chiefs and San Francisco 49ers are set to face off in Super Bowl 2020."],
    # "what_time": [
    #     "The Super Bowl in 2020, the game that will crown an NFL champion for the 2019 season, is scheduled"
    #     " to take place Sunday, February 2 at Hard Rock Stadium in Miami Gardens, Florida."
    #     " The 49ers will play the Chiefs."
    # ],
    "fun_facts": fun_facts,
    "talk_about": fun_facts,
    "forty_niner": forty_niner_fun_facts,
    "chiefs": chiefs_fun_facts,
    "what_about": fun_facts,
    "super_bowl": fun_facts,
}
dialog_segment_regs = compile_regs(dialog_segment_regs)


def dialog_segment_handler(last_utter):
    response = ""
    confidence = 0.0
    curr_user_uttr = last_utter.lower()

    active_segments = [
        segment_name for segment_name, segment_reg in dialog_segment_regs.items() if segment_reg.search(curr_user_uttr)
    ]
    logger.info(f"active_segments: {active_segments}")
    if active_segments:
        response = random.choice(faq_candidetes[active_segments[0]])
        confidence = 1.0 if len(active_segments) > 1 else 0.8
    return response, confidence


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
