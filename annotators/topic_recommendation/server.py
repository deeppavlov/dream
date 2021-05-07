import logging
import time
import pickle
import json
import numpy as np
from os import getenv

from flask import Flask, request, jsonify
import sentry_sdk

sentry_sdk.init(getenv("SENTRY_DSN"))


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

topic2skills = json.load(open("topic2skills.json"))

MODEL_PATH = getenv("MODEL_PATH")
TOP_K = 3

TOPICS = [
    "ordinal",
    "albumname",
    "genre",
    "sportteam",
    "songname",
    "vehicle",
    "event",
    "wear",
    "channelname",
    "party",
    "person",
    "sport",
    "venue",
    "gamename",
    "position",
    "softwareapplication",
    "bookname",
    "device",
    "videoname",
    "location",
    "sportrole",
    "organization",
]

embeddings = np.identity(len(TOPICS)).tolist()
topics_embeddings = {topic: emb for topic, emb in zip(TOPICS, embeddings)}

try:
    with open(MODEL_PATH, "rb") as file:
        model = pickle.load(file)
    model.predict_proba([embeddings[0] * 3])
    logger.info("test query processed")
except Exception as exc:
    sentry_sdk.capture_exception(exc)
    logger.exception(exc)
    raise exc


def choose_candidate_topics(current_topics, context_topics):
    if len(context_topics) > 0:
        history_embedding = sum(np.array([topics_embeddings[topic] for topic in context_topics if topic in TOPICS]))
        normalized_history_embedding = (history_embedding / sum(history_embedding)).tolist()
    else:
        normalized_history_embedding = [0] * len(TOPICS)
    if len(current_topics) > 0:
        current_topic_embeddings = [topics_embeddings[topic] for topic in current_topics]
    else:
        current_topic_embeddings = [[0] * len(TOPICS)]
    samples = []
    for topic_emb in current_topic_embeddings:
        for topic, embedding in topics_embeddings.items():
            samples.append({"topic": topic, "embedding": topic_emb + embedding + normalized_history_embedding})
    samples_embeddings = [el["embedding"] for el in samples]
    preds = model.predict_proba(samples_embeddings)[:, 1]
    top_idx = np.argsort(preds)[::-1][:TOP_K]
    candidate_topics = [el["topic"] for i, el in enumerate(samples) if i in top_idx]
    candidate_topics = list(set(candidate_topics))
    return candidate_topics


def get_entities(utter_entities):
    all_entities = sum(utter_entities, [])
    all_entities = [ent.get("label", "") for ent in all_entities]
    all_entities = [ent for ent in all_entities if ent in TOPICS]
    return all_entities


def handler(requested_data):
    st_time = time.time()

    utter_entities_batch = requested_data["utter_entities_batch"]
    responses = []
    for utter_entities in utter_entities_batch:
        try:
            context_topics = get_entities(utter_entities)
            current_topics = get_entities(utter_entities[-1:])
            candidate_topics = choose_candidate_topics(current_topics, context_topics)
            candidate_topics = sum([topic2skills.get(topic, []) for topic in candidate_topics], [])
            responses.append(candidate_topics)
        except Exception as exc:
            logger.exception(exc)
            sentry_sdk.capture_exception(exc)
            responses.append([])

    total_time = time.time() - st_time
    logger.info(f"topic_recommendation exec time: {total_time:.3f}s")
    return responses


@app.route("/respond", methods=["POST"])
def respond():
    response = handler(request.json)
    return jsonify(response)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
