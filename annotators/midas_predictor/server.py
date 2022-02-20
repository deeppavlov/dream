import logging
import os
import pickle5 as pickle
import time

import sentry_sdk
import tensorflow_hub as hub
from flask import Flask, jsonify, request

from midas_dataset import MidasVectorizer


sentry_sdk.init(os.getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Load data (deserialize)
with open("/data/models/midas_predictor_rfc_depth20.pickle", "rb") as f:
    rfc_model = pickle.load(f)


TFHUB_CACHE_DIR = os.environ.get("TFHUB_CACHE_DIR", None)
if TFHUB_CACHE_DIR is None:
    os.environ["TFHUB_CACHE_DIR"] = "/root/tfhub_cache"

USE_MODEL_PATH = os.environ.get("USE_MODEL_PATH", None)
if USE_MODEL_PATH is None:
    USE_MODEL_PATH = "https://tfhub.dev/google/universal-sentence-encoder/4"

encoder = hub.load(USE_MODEL_PATH)

Midas2Id = {
    "appreciation": 0,
    "command": 1,
    "comment": 2,
    "complaint": 3,
    "dev_command": 4,
    "neg_answer": 5,
    "open_question_factual": 6,
    "open_question_opinion": 7,
    "opinion": 8,
    "other_answers": 9,
    "pos_answer": 10,
    "statement": 11,
    "yes_no_question": 12,
}

midas_vectorizer = MidasVectorizer(
    text_vectorizer=encoder, midas2id=Midas2Id, context_len=3, embed_dim=512  # USE  # USE vector size
)


def inference(context: list, midas: list):
    """
    context: list of utterances (string)
    midas: list of lists of midas dicts {midas_label_1: prob, ..., midas_label_n, proba}
            1D : number of utterances = 3, 2D: number of sentences in the utterance: N

    output: probability distribution for the next utterance
    """
    global rfc_model, midas_vectorizer
    # extract vectors
    midas_vectors = list()

    for ut in midas:
        utterance_vec = list()
        for sent in ut:
            utterance_vec.append(list(sent.values()))
        midas_vectors.append(utterance_vec)

    assert len(context) == len(midas_vectors)
    vec = midas_vectorizer.context_vector(context, midas_vectors)[None, :]
    pred_probas = rfc_model.predict_proba(vec)

    return pred_probas[0]


test_sample = (
    "Yeah I think the original is going to be the best. Did you know that Stephen King actually thinks "
    "that the movie Bambi should be a horror movie?"
)
test_midas = [
    {
        "appreciation": 0.0022430846001952887,
        "command": 0.0024833311326801777,
        "comment": 0.007560018915683031,
        "complaint": 0.0010543332900851965,
        "dev_command": 0.001281813019886613,
        "neg_answer": 0.0013224049471318722,
        "open_question_factual": 0.0015646334504708648,
        "open_question_opinion": 0.0012719057267531753,
        "opinion": 0.9702610373497009,
        "other_answers": 0.0010310874786227942,
        "pos_answer": 0.0032127194572240114,
        "statement": 0.005328143946826458,
        "yes_no_question": 0.001385452225804329,
    },
    {
        "appreciation": 0.01672188937664032,
        "command": 0.08160554617643356,
        "comment": 0.020263012498617172,
        "complaint": 0.0159416776150465,
        "dev_command": 0.05004351958632469,
        "neg_answer": 0.0061445110477507114,
        "open_question_factual": 0.011150079779326916,
        "open_question_opinion": 0.012583243660628796,
        "opinion": 0.020224809646606445,
        "other_answers": 0.006914180237799883,
        "pos_answer": 0.048117928206920624,
        "statement": 0.2340209186077118,
        "yes_no_question": 0.47626861929893494,
    },
]

print(f"test sample proceeded result: {inference([test_sample], [test_midas])}")
logger.info("midas-predictor is loaded")


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    # each sample is a list of 3 utterances texts (no sentence segmentation)
    utterances = request.json["utterances"]
    # each sample is a list of midas distributions where the number of distributions is equal to number of sentences
    midas_distributions = request.json["midas_distributions"]

    result = [inference(utts, dists) for utts, dists in zip(utterances, midas_distributions)]
    result = [{k: s for k, s in zip(Midas2Id.keys(), sample)} for sample in result]

    total_time = time.time() - st_time
    logger.info(f"midas-predictor exec time: {total_time:.3f}s")
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
