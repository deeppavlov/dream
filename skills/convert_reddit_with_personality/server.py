import logging
import os
import random
import pickle
import time
import json

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
filter = json.load(open("./banned_responses.json"))

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
    return (confidences <= confidence).sum() / len(confidences)
    # return float(confidence)


def tokenize(sentence):
    filtered_sentence = re.sub("[^A-Za-z0-9]+", " ", sentence).split()
    filtered_sentence = [token for token in filtered_sentence if len(token) > 2]
    return set(filtered_sentence)


unanswered_utters = ["let's talk about", "what else can you do?", "let's talk about books"]
unanswered_utters = [tokenize(utter) for utter in unanswered_utters]


def is_unanswerable_utters(history):
    last_utter = tokenize(history[-1])
    for utter in unanswered_utters:
        if len(last_utter & utter) / len(last_utter | utter) > 0.9:
            return True


def clear_answer(answer):
    answer = re.sub("[^A-Za-z0-9-!,.’&?'\"’ ]+", "", answer).strip()
    answer = re.sub(' +', ' ', answer)
    return answer


topic_personality = {"Literature": "My favourite book is Walk in the Woods by Bill Bryson",
                     "Art_Event": "I like visiting museums",
                     "Celebrities": "My favorite famous person is Neil deGrasse Tyson",
                     "Entertainment": "My hobby is 3d printing",
                     "Fashion": "I like to wear some warm shirt or coats",
                     "Food_Drink": "Rice and beans is my favourite food",
                     "Games": "My favourite game is Minecraft",
                     "Math": "I have always figure or find out why concepts and equations work",
                     "Movies_TV": "My favorite movie is Matrix",
                     "News": "I'm interested in news about technology",
                     "Music": "I'm a big fan of a music band the Queen",
                     "Pets_Animals": "I have one pet which is a dog",
                     "SciTech": "I'm interested in physics and astronomy",
                     "Sports": "My favourite sport game is basketball",
                     "Travel_Geo": "I have visited Alaska, Norway, Germany, Hawaii and Poland",
                     "Weather_Time": "",
                     "Phatic": "",
                     "Politics": "",
                     "Psychology": "",
                     "Religion": "",
                     "Sex_Profanity": "",
                     "Other": ""}


def get_character(topics):
    characters = [topic_personality[topic] for topic in topics]
    return characters


def inference(utterances_histories, topics):
    if len(topics) > 0:
        characters = get_character(topics)
    else:
        characters = [""]
    if len(characters[0]) > 0:
        utterances_with_character = list(characters) + [utterances_histories[-1]]
        context_encoding = encode_context(utterances_with_character)
    else:
        context_encoding = encode_context(utterances_histories)
    scores = context_encoding.dot(response_encodings.T)
    indices = np.argsort(scores)[::-1][:10]
    filtered_indices = [ind for ind in indices if responses[ind] not in filter]

    if is_unanswerable_utters(utterances_histories):
        return "", 0.0

    clear_utterances_histories = [tokenize(utt) for utt in utterances_histories[1::2]]

    for ind in reversed(filtered_indices):
        tokenized_response = tokenize(responses[ind])
        if (len(tokenized_response) < 4 or len(tokenized_response) > 15) and len(characters[0]) == 0:
            filtered_indices.remove(ind)
        elif len(tokenized_response) == 0:
            filtered_indices.remove(ind)
        else:
            for utterance in clear_utterances_histories:
                if len(tokenized_response & utterance) / len(tokenized_response) > 0.6:
                    filtered_indices.remove(ind)
                    break

    if len(filtered_indices) > 0:
        return clear_answer(responses[filtered_indices[0]]), approximate_confidence(scores[filtered_indices[0]])
    else:
        return "", 0.0


@app.route("/respond", methods=["POST"])
@swag_from("chitchat_endpoint.yml")
def convert_chitchat_model():
    st_time = time.time()
    topics_batch = [topics.get("text", []) for topics in request.json["topics"]]
    utterances_histories = request.json["utterances_histories"]
    response = [inference(hist, topics) for hist, topics in zip(utterances_histories, topics_batch)]
    total_time = time.time() - st_time
    logger.warning(f"convert_reddit exec time: {total_time:.3f}s")
    return jsonify(response)
