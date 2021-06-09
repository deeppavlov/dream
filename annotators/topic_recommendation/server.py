import logging
import time
import os

import numpy as np
from flask import Flask, request, jsonify
import sentry_sdk

from convert import encode_contexts, encode_responses
from common.link import LIST_OF_SCRIPTED_TOPICS, skills_phrases_map

sentry_sdk.init(os.getenv("SENTRY_DSN"))


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

TOP_K = 3

skills2responses = {topic: skills_phrases_map[topic] for topic in LIST_OF_SCRIPTED_TOPICS}

responses2skills = {response: skill for skill, responses in skills2responses.items() for response in responses}
responses = list(responses2skills.keys())

response_encodings = encode_responses(responses)


def get_ranked_list(context):
    logger.warning(context)
    context_encoding = encode_contexts(context)
    scores = context_encoding.dot(response_encodings.T)
    top_indices = np.argsort(scores)[::-1]
    return top_indices[0]


def handler(requested_data):
    st_time = time.time()

    utter_sentences_batch = requested_data["utterances_histories"]
    candidate_topics_batch = []
    for utter_sentences in utter_sentences_batch:
        try:
            topic_ranked_list = get_ranked_list(utter_sentences)
            candidate_topics = list(set([responses2skills[responses[i]] for i in topic_ranked_list[:TOP_K]]))
            candidate_topics_batch.append(candidate_topics)
        except Exception as exc:
            logger.exception(exc)
            sentry_sdk.capture_exception(exc)
            candidate_topics_batch.append([])

    total_time = time.time() - st_time
    logger.info(f"topic_recommendation exec time: {total_time:.3f}s")
    logger.warning(candidate_topics_batch)
    return candidate_topics_batch


@app.route("/respond", methods=["POST"])
def respond():
    response = handler(request.json)
    return jsonify(response)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
