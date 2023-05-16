import json
import logging
import requests
import time
from os import getenv, listdir
from pathlib import Path

import numpy as np
import sentry_sdk
from flask import Flask, request, jsonify


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)
app = Flask(__name__)

SENTENCE_RANKER_SERVICE_URL = getenv("SENTENCE_RANKER_SERVICE_URL")
logger.info(f"prompt-selector considered ranker: {SENTENCE_RANKER_SERVICE_URL}")
N_SENTENCES_TO_RETURN = int(getenv("N_SENTENCES_TO_RETURN"))
# list of string names of prompts from common/prompts
PROMPTS_TO_CONSIDER = getenv("PROMPTS_TO_CONSIDER", "").split(",")
logger.info(f"prompt-selector considered prompts: {PROMPTS_TO_CONSIDER}")
PROMPTS = []
PROMPTS_NAMES = []
for filename in listdir("common/prompts"):
    prompt_name = Path(filename).stem
    if ".json" in filename and prompt_name in PROMPTS_TO_CONSIDER:
        data = json.load(open(f"common/prompts/{filename}", "r"))
        PROMPTS.append(data.get("goals", ""))
        PROMPTS_NAMES.append(prompt_name)


def get_result(request):
    global PROMPTS, PROMPTS_NAMES
    st_time = time.time()
    contexts = request.json["contexts"]
    prompts_goals_from_attributes = request.json["prompts_goals"]

    result = []
    pairs = []
    context_ids = []

    for context_id, context in enumerate(contexts):
        if len(context[-1].split()) < 5:
            str_context = "\n".join(context[-3:])
        else:
            str_context = context[-1]
        for prompt_goals, prompt_name in zip(PROMPTS, PROMPTS_NAMES):

            pairs += [[str_context, prompts_goals_from_attributes[context_id].get(prompt_name, "") if not prompt_goals else prompt_goals]]
            context_ids += [context_id]
    context_ids = np.array(context_ids)
    if any([len(pair[1]) == 0 for pair in pairs]):
        logger.info("Some goals from prompts are empty. Skip ranking.")
        result = [{"prompts": [], "max_similarity": 0.0}] * len(contexts)
    else:
        try:
            scores = requests.post(SENTENCE_RANKER_SERVICE_URL, json={"sentence_pairs": pairs}, timeout=1.5).json()[0][
                "batch"
            ]
            scores = np.array(scores)
            for i, context in enumerate(contexts):
                curr_ids = np.where(context_ids == i)[0]
                most_relevant_sent_ids = np.argsort(scores[curr_ids])[::-1][:N_SENTENCES_TO_RETURN]
                curr_result = {
                    "prompts": [PROMPTS_NAMES[_id] for _id in most_relevant_sent_ids],
                    "max_similarity": scores[curr_ids][most_relevant_sent_ids[0]],
                }
                result += [curr_result]
        except Exception as exc:
            logger.exception(exc)
            sentry_sdk.capture_exception(exc)
            result = [{"prompts": [], "max_similarity": 0.0}] * len(contexts)

    total_time = time.time() - st_time
    logger.info(f"prompt-selector exec time: {total_time:.3f}s")
    logger.info(f"prompt-selector result: {result}")
    return result


@app.route("/respond", methods=["POST"])
def respond():
    result = get_result(request)
    return jsonify(result)


@app.route("/respond_batch", methods=["POST"])
def respond_batch():
    result = get_result(request)
    return jsonify([{"batch": result}])


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
