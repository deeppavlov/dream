import logging
import time
import os
import pickle

import numpy as np
from flask import Flask, request, jsonify
import sentry_sdk

sentry_sdk.init(os.getenv("SENTRY_DSN"))


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

DATABASE_PATH = os.getenv("DATABASE_PATH")

TOP_V = 3
TOP_K = 3

scenario_skills = [
    "dff_animals_skill",
    "news_api_skill",
    "dff_food_skill",
    "dff_travel_skill",
    "dff_sport_skill",
    "dff_science_skill",
    "dff_music_skill",
    "game_cooperative_skill",
    "book_skill",
    "dff_movie_skill",
    "dff_gossip_skill",
]

topic2skill = {
    "Movies_TV": "dff_movie_skill",
    "Music": "dff_music_skill",
    "SciTech": "dff_science_skill",
    "Literature": "book_skill",
    "Travel_Geo": "dff_travel_skill",
    "Celebrities": "dff_gossip_skill",
    "Games": "game_cooperative_skill",
    "Pets_Animals": "dff_animals_skill",
    "Sports": "dff_sport_skill",
    "Food_Drink": "dff_food_skill",
    "News": "news_api_skill",
}


with open(DATABASE_PATH, "rb") as f:
    database = pickle.load(f)


def get_candidate_topics(embedding):
    scores = np.array(embedding).dot(np.array(database).T)
    top_indices = np.argsort(scores)[::-1]
    similarity_vector = np.sum(np.array([database[top_idx] for top_idx in top_indices[:TOP_V]]), 0)
    candidate_topics_idx = np.argsort(similarity_vector)[::-1][:TOP_K]
    candidate_topics = [scenario_skills[idx] for idx in candidate_topics_idx]
    return candidate_topics


def handler(requested_data):
    st_time = time.time()
    logger.warning(requested_data)

    active_skills_batch = requested_data["active_skills"]
    cobot_topics_batch = requested_data["cobot_topics"]

    candidate_topics_batch = []

    for active_skills, cobot_topics in zip(active_skills_batch, cobot_topics_batch):
        try:
            skills_dict = {skill: 0 for skill in scenario_skills}

            for skill in active_skills:
                if skill in scenario_skills:
                    skills_dict[skill] += 1

            for topic in cobot_topics:
                if topic in topic2skill.keys():
                    skill = topic2skill[topic]
                    skills_dict[skill] += 1

            total_skill = sum(skills_dict.values())
            embedding = [skills_dict[skill] / total_skill if total_skill > 0 else 0 for skill in scenario_skills]
            used_topics = [skill for skill in scenario_skills if skills_dict[skill] > 0]
            candidate_topics = get_candidate_topics(embedding)
            candidate_topics = [skill for skill in candidate_topics if skill not in used_topics]
            if "game_cooperative_skill" in candidate_topics:
                candidate_topics += ["dff_gaming_skill"]
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
