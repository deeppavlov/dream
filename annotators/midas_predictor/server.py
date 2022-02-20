import logging
import os
import pickle
import time
import uuid

import sentry_sdk
import tensorflow_hub as hub
from flask import Flask, jsonify, request
from sentry_sdk.integrations.logging import ignore_logger

from utils.midas_dataset import MidasDataset, MidasVectorizer


ignore_logger("root")
sentry_sdk.init(os.getenv("SENTRY_DSN"))
app = Flask(__name__)
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Load data (deserialize)
with open('models/midas_predictor_rfc_depth20.pickle', 'rb') as f:
    rfc_model = pickle.load(f)

os.environ['TFHUB_CACHE_DIR'] = './models/tf_cache'
module_url = "https://tfhub.dev/google/universal-sentence-encoder/4"
encoder = hub.load(module_url)

Midas2Id = {
    "appreciation": 0, "command": 1, "comment": 2,"complaint": 3,
    "dev_command": 4, "neg_answer": 5, "open_question_factual": 6,
    "open_question_opinion": 7, "opinion": 8, "other_answers": 9,
    "pos_answer": 10, "statement": 11, "yes_no_question": 12,
}

midas_vectorizer = MidasVectorizer(
    text_vectorizer=encoder,  # USE
    midas2id=Midas2Id,
    context_len=3,
    embed_dim=512  # USE vector size
)


def inference(context: list, midas: list, clf, vectorizer):
    """
    context: list of utterances (string)
    midas: list of lists of midas dicts {midas_label_1: prob, ..., midas_label_n, proba}
            1D : number of utterances = 3, 2D: number of sentences in the utterance: N
    clf: sklearn classifier train to predict next midas label
    vectorizer: Vectorizer to concatenate text embeddings with midas proba distribution

    output: probability distribution for the next utterance
    """
    # extract vectors
    midas_vectors = list()

    for ut in midas:
        utterance_vec = list()
        for sent in ut:
            utterance_vec.append(list(sent.values()))
        midas_vectors.append(utterance_vec)

    assert len(context) == len(midas_vectors)
    vec = vectorizer.context_vector(context, midas_vectors)[None, :]
    pred_probas = clf.predict_proba(vec)

    return pred_probas[0]


test_sample = "Yeah I think the original is going to be the best. Did you know that Stephen King actually thinks " \
              "that the movie Bambi should be a horror movie?"
test_midas = [{'appreciation': 0.0022430846001952887, 'command': 0.0024833311326801777,
               'comment': 0.007560018915683031, 'complaint': 0.0010543332900851965,
               'dev_command': 0.001281813019886613, 'neg_answer': 0.0013224049471318722,
               'open_question_factual': 0.0015646334504708648, 'open_question_opinion': 0.0012719057267531753,
               'opinion': 0.9702610373497009, 'other_answers': 0.0010310874786227942,
               'pos_answer': 0.0032127194572240114, 'statement': 0.005328143946826458,
               'yes_no_question': 0.001385452225804329},
              {'appreciation': 0.01672188937664032, 'command': 0.08160554617643356, 'comment': 0.020263012498617172,
               'complaint': 0.0159416776150465, 'dev_command': 0.05004351958632469,
               'neg_answer': 0.0061445110477507114, 'open_question_factual': 0.011150079779326916,
               'open_question_opinion': 0.012583243660628796, 'opinion': 0.020224809646606445,
               'other_answers': 0.006914180237799883, 'pos_answer': 0.048117928206920624,
               'statement': 0.2340209186077118, 'yes_no_question': 0.47626861929893494}]

print(f"test sample proceeded result: {inference([test_sample], [test_midas], rfc_model, midas_vectorizer)}")
logger.info(f"midas-predictor is loaded")


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    user_sentences = request.json["sentences"]
    session_id = uuid.uuid4().hex

    sentseg_result = []
    # Only for user response delete alexa from sentence TRELLO#275
    if len(user_sentences) % 2 == 1:
        user_sent_without_alexa = re.sub(r"(^alexa\b)", "", user_sentences[-1], flags=re.I).strip()
        if len(user_sent_without_alexa) > 1:
            user_sentences[-1] = user_sent_without_alexa

    for i, text in enumerate(user_sentences):
        if text.strip():
            logger.info(f"user text: {text}, session_id: {session_id}")
            sentseg = model.predict(sess, text)
            sentseg = sentseg.replace(" '", "'")
            sentseg = preprocessing(sentseg)
            segments = split_segments(sentseg)
            sentseg_result += [{"punct_sent": sentseg, "segments": segments}]
            logger.info(f"punctuated sent. : {sentseg}")
        else:
            sentseg_result += [{"punct_sent": "", "segments": [""]}]
            logger.warning(f"empty sentence {text}")
    total_time = time.time() - st_time
    logger.info(f"sentseg exec time: {total_time:.3f}s")
    return jsonify(sentseg_result)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
