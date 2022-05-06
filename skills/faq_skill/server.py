
import logging
from os import getenv
from time import time

import sentry_sdk
from flask import Flask, request, jsonify
from deeppavlov import build_model


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CONFIG_NAME = getenv("CONFIG_NAME", None)
if CONFIG_NAME is None:
    raise NotImplementedError("No FAQ config name is given.")

try:
    faq_model = build_model(CONFIG_NAME)
except Exception as e:
    logger.warning(e)
    sentry_sdk.capture_message(e)


def get_faq_response(dialogs):
    dialogue_contexts = []
    for dialog in dialogs:
        context = ""
        for uttr in dialog["utterances"][-3]:
            context += f" {uttr['text']}"
        dialogue_contexts += [context]
    pred_responses, pred_probas = faq_model(dialogue_contexts)
    return pred_responses, pred_probas

 
@app.route("/respond", methods=["POST"])
def respond():
    st_time = time()
    dialogs = request.json["dialogs"]
    responses, confidences = get_faq_response(dialogs)
    attributes = [{"response_parts": ["body"]}] * len(dialogs)

    total_time = time() - st_time
    logger.info(f"faq-skill exec time: {total_time:.3f}s")
    return jsonify(list(zip(responses, confidences, attributes)))


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
