#!/usr/bin/env python

import logging
import numpy as np
import time
import requests

from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk


sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

BADLIST_URL = getenv("BADLIST_ANNOTATOR_URL", "http://badlisted-words:8018/badlisted_words_batch")
FILTER_BADLISTED_WORDS = getenv("FILTER_BADLISTED_WORDS", 0)


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    dialogs = request.json["dialogs"]
    response_candidates = [dialog["utterances"][-1]["hypotheses"] for dialog in dialogs]

    selected_skill_names = []
    selected_responses = []
    selected_confidences = []

    for i, dialog in enumerate(dialogs):
        confidences = []
        responses = []
        skill_names = []

        for skill_data in response_candidates[i]:
            if skill_data["text"] and skill_data["confidence"]:
                logger.info(f"Skill {skill_data['skill_name']} returned non-empty hypothesis with non-zero confidence.")

            if FILTER_BADLISTED_WORDS:
                try:
                    badlist_result = requests.post(
                        BADLIST_URL, json={"sentences": [skill_data["text"]]}, timeout=1.5
                    ).json()[0]["batch"][0]
                except Exception as exc:
                    logger.exception(exc)
                    sentry_sdk.capture_exception(exc)
                    badlist_result = {"bad_words": False}
                if not badlist_result["bad_words"]:
                    confidences += [skill_data["confidence"]]
                    responses += [skill_data["text"]]
                    skill_names += [skill_data["skill_name"]]
            else:
                confidences += [skill_data["confidence"]]
                responses += [skill_data["text"]]
                skill_names += [skill_data["skill_name"]]

        best_id = np.argmax(confidences)

        selected_skill_names.append(skill_names[best_id])
        selected_responses.append(responses[best_id])
        selected_confidences.append(confidences[best_id])

    total_time = time.time() - st_time
    logger.info(f"confidence_based_response_selector exec time = {total_time:.3f}s")
    return jsonify(list(zip(selected_skill_names, selected_responses, selected_confidences)))


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
