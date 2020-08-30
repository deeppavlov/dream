import logging
import os
import random
import pickle
import time
import json
import pathlib

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

topics = [
    "book",
    "entertainment",
    "fashion",
    "movie",
    "music",
    "politics",
    "science_technology",
    "sport",
    "animals",
]


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
dataset = {topic: pickle.load(open(DATABASE_PATH.replace("*", topic), "rb")) for topic in topics}
np_load_old = np.load

if pathlib.Path(CONFIDENCE_PATH).is_file():
    confidences = np.load(CONFIDENCE_PATH, allow_pickle=True)
else:
    confidences = None
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


def approximate_confidence(confidence, approximate_confidence_is_enabled=True):
    if approximate_confidence_is_enabled:
        return 0.95 * ((confidences <= confidence).sum() / len(confidences))
    else:
        return float(confidence)


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
    answer = re.sub("[^A-Za-z0-9-!,.’?'\"’ ]+", "", answer).strip()
    answer = re.sub(" +", " ", answer)
    return answer


movie_cobot_dialogacts = {
    "Entertainment_Movies",
    "Sports",
    "Entertainment_Music",
    "Entertainment_General",
    "Phatic",
}
movie_cobot_topics = {
    "Movies_TV",
    "Celebrities",
    "Art_Event",
    "Entertainment",
    "Fashion",
    "Games",
    "Music",
    "Sports",
}
entertainment_cobot_dialogacts = {
    "Entertainment_Movies",
    "Entertainment_Music",
    "Entertainment_General",
    "Entertainment_Books",
}
entertainment_cobot_topics = {
    "Art_Event",
    "Celebrities",
    "Entertainment",
    "Games",
}
fashion_cobot_dialogacts = set()
fashion_cobot_topics = {
    "Fashion",
}
science_cobot_dialogacts = {
    "Science_and_Technology",
    "Entertainment_Books",
}
science_cobot_topics = {
    "Literature",
    "Math",
    "SciTech",
}
science_cobot_dialogacts = {
    "Science_and_Technology",
    "Entertainment_Books",
}
science_cobot_topics = {
    "Literature",
    "Math",
    "SciTech",
}
politic_cobot_dialogacts = {
    "Politics",
}
politic_cobot_topics = {
    "Politics",
}
sport_cobot_dialogacts = {
    "Sports",
}
sport_cobot_topics = {
    "Sports",
}
animals_cobot_topics = {
    "Pets_Animals",
}
books_cobot_dialogacts = {"Entertainment_General", "Entertainment_Books"}
books_cobot_topics = {"Entertainment", "Literature"}
news_cobot_topics = {"News"}


def select_topics(agent_dialogacts, agent_topics):
    agent_dialogacts, agent_topics = set(agent_dialogacts), set(agent_topics)
    about_movies = (movie_cobot_dialogacts & agent_dialogacts) | (movie_cobot_topics & agent_topics)
    about_music = ("Entertainment_Music" in agent_dialogacts) | ("Music" in agent_topics)
    about_books = (books_cobot_dialogacts & agent_dialogacts) | (books_cobot_topics & agent_topics)
    about_entertainments = (entertainment_cobot_dialogacts & agent_dialogacts) | (
        entertainment_cobot_topics & agent_topics
    )
    about_fashions = (fashion_cobot_dialogacts & agent_dialogacts) | (fashion_cobot_topics & agent_topics)
    # about_politics = (politic_cobot_dialogacts & agent_dialogacts) | (sport_cobot_topics & agent_topics)
    about_science_technology = (science_cobot_dialogacts & agent_dialogacts) | (science_cobot_topics & agent_topics)
    about_sports = (sport_cobot_dialogacts & agent_dialogacts) | (sport_cobot_topics & agent_topics)
    about_animals = animals_cobot_topics & agent_topics
    topics = []
    if about_movies:
        topics.append("movie")
    if about_music:
        topics.append("music")
    if about_books:
        topics.append("book")
    if about_entertainments:
        topics.append("entertainment")
    if about_fashions:
        topics.append("fashion")
    # if about_politics:
    #     topics.append("politics")
    if about_science_technology:
        topics.append("science_technology")
    if about_sports:
        topics.append("sport")
    if about_animals:
        topics.append("animals")
    return topics


def inference(utterances_histories, topic, approximate_confidence_is_enabled=True):
    if not (topic in dataset):
        return "", 0.0, {"topic": topic}
    response_encodings, responses = dataset[topic]
    context_encoding = encode_context(utterances_histories)
    scores = context_encoding.dot(response_encodings.T)
    indices = np.argsort(scores)[::-1][:10]
    filtered_indices = [ind for ind in indices if responses[ind] not in filter]

    if is_unanswerable_utters(utterances_histories):
        return "", 0.0, {"topic": topic}

    clear_utterances_histories = [tokenize(utt) for utt in utterances_histories[1::2]]

    for ind in reversed(filtered_indices):
        tokenized_response = tokenize(responses[ind])
        if len(tokenized_response) < 4 or len(tokenized_response) > 15:
            filtered_indices.remove(ind)
        else:
            for utterance in clear_utterances_histories:
                if len(tokenized_response & utterance) / len(tokenized_response) > 0.6:
                    filtered_indices.remove(ind)
                    break

    if len(filtered_indices) > 0:
        return (
            clear_answer(responses[filtered_indices[0]]),
            approximate_confidence(scores[filtered_indices[0]], approximate_confidence_is_enabled),
            {"topic": topic},
        )
    else:
        return "", 0.0, {"topic": topic}


def choose_best_answer(utterances_histories, topics, approximate_confidence_is_enabled=True):
    logger.warning(f"topics {topics}")
    answers = [inference(utterances_histories, topic, approximate_confidence_is_enabled) for topic in topics]
    logger.warning(f"answers {answers}")
    if approximate_confidence_is_enabled:
        return sorted(answers, key=lambda x: -x[1])[0] if answers else ("", 0.0)
    else:
        return answers


@app.route("/respond", methods=["POST"])
@swag_from("chitchat_endpoint.yml")
def convert_chitchat_model():
    st_time = time.time()
    logger.warning(f"request.json = {request.json}")
    # get utterances_histories
    utterances_histories = request.json["utterances_histories"]
    # get dialogact_topics
    act_topic_batch = request.json["dialogact_topics"]
    # get topics
    topic_batch = [topics["text"] for topics in request.json["topics"]]
    # get approximate_confidence_is_enabled
    approximate_confidence_is_enabled = request.json.get("approximate_confidence_is_enabled", True)
    # logger.warning(f"utterances_histories {utterances_histories}")
    # logger.warning(f"act_topic_batch {act_topic_batch}")
    # logger.warning(f"topic_batch {topic_batch}")
    response = [
        choose_best_answer(hist, select_topics(act_topic, topics), approximate_confidence_is_enabled)
        for hist, act_topic, topics in zip(utterances_histories, act_topic_batch, topic_batch)
    ]
    total_time = time.time() - st_time
    logger.warning(f"response {response}")
    logger.warning(f"topicalchat_convert_retrieval exec time: {total_time:.3f}s")
    return jsonify(response)
