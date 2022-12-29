import logging
import requests
import time
from os import getenv, listdir
import json

import numpy as np
import sentry_sdk
from flask import Flask, request, jsonify
import re


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)
app = Flask(__name__)

SENTENCE_RANKER_SERVICE_URL = getenv("SENTENCE_RANKER_SERVICE_URL")
N_SENTENCES_TO_RETURN = int(getenv("N_SENTENCES_TO_RETURN"))
PROMPTS = []
for filename in listdir("common/prompts"):
    data = json.load(open("common/prompts/" + filename, "r"))
    PROMPTS.append(data["prompt"])


def get_result(request, questions_only=False):
    st_time = time.time()
    contexts = request.json["contexts"]
    result = []
    pairs = []
    context_ids = []

    for context_id, context in enumerate(contexts):
        str_context = " ".join(context)
        for prompt in PROMPTS:
            if questions_only:
                questions = re.findall(r"\nQuestion: (.*)\nAnswer:", prompt)
                questions_list = " ".join(questions)
                pairs += [[str_context, questions_list]]
            else:
                pairs += [[str_context, prompt]]
            context_ids += [context_id]
    context_ids = np.array(context_ids)
    try:
        scores = requests.post(SENTENCE_RANKER_SERVICE_URL, json={"sentence_pairs": pairs}, timeout=1.5).json()[0][
            "batch"
        ]
        scores = np.array(scores)
        for i, context in enumerate(contexts):
            curr_ids = np.where(context_ids == i)[0]
            most_relevant_sent_ids = np.argsort(scores[curr_ids])[::-1][:N_SENTENCES_TO_RETURN]
            curr_result = {
                "prompt": [PROMPTS[_id] for _id in most_relevant_sent_ids],
                "max_similarity": scores[curr_ids][most_relevant_sent_ids[0]],
            }
            result += [curr_result]
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        result = [{"prompt": [], "max_similarity": 0.0}] * len(contexts)

    total_time = time.time() - st_time
    logger.info(f"propmt-selector exec time: {total_time:.3f}s")
    return result


@app.route("/respond", methods=["POST"])
def respond():
    result = get_result(request, questions_only=True)
    return jsonify(result)


@app.route("/respond_batch", methods=["POST"])
def respond_batch():
    result = get_result(request, questions_only=True)
    return jsonify([{"batch": result}])


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
