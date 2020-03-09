import logging
import os
import random
import pickle
import time
import json
import difflib

import tensorflow_hub as tfhub
import tensorflow as tf
import tensorflow_text
import numpy as np
import re
from flask import Flask, request, jsonify
from flasgger import Swagger, swag_from
import sentry_sdk

tensorflow_text.__name__

SENTRY_DSN = os.getenv("SENTRY_DSN")
SEED = 31415
MODEL_PATH = os.getenv("MODEL_PATH")
DATABASE_PATH = os.getenv("DATABASE_PATH")
CONFIDENCE_PATH = os.getenv("CONFIDENCE_PATH")


sentry_sdk.init(SENTRY_DSN)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(module)s %(lineno)d %(levelname)s : %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

app = Flask(__name__)
swagger = Swagger(app)

random.seed(SEED)

sess = tf.InteractiveSession(graph=tf.Graph())

module = tfhub.Module(MODEL_PATH)
response_encodings, responses = pickle.load(open(DATABASE_PATH, "rb"))
confidences = np.load(CONFIDENCE_PATH)


spaces_pat = re.compile(r"\s+")
special_symb_pat = re.compile(r"[^A-Za-z0-9-!,.’?'\"’ ]")


def clear_answer(text):
    return special_symb_pat.sub("", spaces_pat.sub(" ", text.lower().replace("\n", " "))).strip()


filter = json.load(open("./banned_responses.json"))
filter = [clear_answer(utter) for utter in filter]

text_placeholder = tf.placeholder(dtype=tf.string, shape=[None])
extra_text_placeholder = tf.placeholder(dtype=tf.string, shape=[None])

# The encode_context signature now also takes the extra context.
context_encoding_tensor = module(
    {"context": text_placeholder, "extra_context": extra_text_placeholder}, signature="encode_context"
)

sess.run(tf.tables_initializer())
sess.run(tf.global_variables_initializer())


def encode_context(dialogue_history):
    """Encode the dialogue context to the response ranking vector space.

    Args:
        dialogue_history: a list of strings, the dialogue history, in
            chronological order.
    """

    # The context is the most recent message in the history.
    context = dialogue_history[-1]

    extra_context = list(dialogue_history[:-1])
    extra_context.reverse()
    extra_context_feature = " ".join(extra_context)

    return sess.run(
        context_encoding_tensor,
        feed_dict={text_placeholder: [context], extra_text_placeholder: [extra_context_feature]},
    )[0]


def approximate_confidence(confidence):
    return 0.95 * (confidences <= confidence).sum() / len(confidences)
    # return float(confidence)


def get_BOW(sentence):
    filtered_sentence = re.sub("[^A-Za-z0-9]+", " ", sentence).split()
    filtered_sentence = [token for token in filtered_sentence if len(token) > 2]
    return set(filtered_sentence)


unanswered_utters = ["let's talk about", "what else can you do?", "let's talk about books"]
unanswered_utters = [get_BOW(utter) for utter in unanswered_utters]


def is_unanswerable_utters(history):
    last_utter = get_BOW(history[-1])
    for utter in unanswered_utters:
        if len(last_utter & utter) / len(last_utter | utter) > 0.9:
            return True


def inference(utterances_histories):
    context_encoding = encode_context(utterances_histories)
    scores = context_encoding.dot(response_encodings.T)
    indices = np.argsort(scores)[::-1][:10]
    filtered_indices = []
    for ind in indices:
        cand = responses[ind]
        if not [
            None
            for f_utter in filter
            if difflib.SequenceMatcher(None, f_utter.split(), clear_answer(cand).split()).ratio() > 0.9
        ]:
            filtered_indices.append(ind)

    if is_unanswerable_utters(utterances_histories):
        return "", 0.0

    clear_utterances_histories = [clear_answer(utt).split() for utt in utterances_histories[::-1][1::2][::-1]]

    for ind in reversed(filtered_indices):
        cand = clear_answer(responses[ind]).split()
        for utterance in clear_utterances_histories:
            if difflib.SequenceMatcher(None, utterance, cand).ratio() > 0.6:
                filtered_indices.remove(ind)
                break

    if len(filtered_indices) > 0:
        return clear_answer(responses[filtered_indices[0]]), approximate_confidence(scores[filtered_indices[0]])
    else:
        return "", 0.0


@app.route("/convert_reddit", methods=["POST"])
@swag_from("chitchat_endpoint.yml")
def convert_chitchat_model():
    st_time = time.time()
    utterances_histories = request.json["utterances_histories"]
    response = [inference(hist) for hist in utterances_histories]
    total_time = time.time() - st_time
    logger.warning(f"convert_reddit exec time: {total_time:.3f}s")
    return jsonify(response)
