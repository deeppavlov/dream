import logging
import time
from os import getenv

from flask import Flask, request, jsonify
import sentry_sdk

from convert import get_ranked_list

sentry_sdk.init(getenv("SENTRY_DSN"))


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

MODEL_PATH = getenv("MODEL_PATH")
TOP_K = 3

topic2response = {"Let's chat about food": "dff_food_skill",
                  "Let's chat about books": "book_skill",
                  "Let's chat about sport": "dff_sport_skill",
                  "Let's chat about movies": "movie_skill",
                  "Let's chat about animals": "dff_animals_skill",
                  "Let's chat about games": "game_cooperative_skill",
                  "Let's chat about music": "dff_music_skill",
                  "Let's chat about news": "news_api_skill",
                  "Let's chat about travels": "dff_travel_skill"}

responses = list(topic2response.keys())


def handler(requested_data):
    st_time = time.time()

    utter_sentences_batch = requested_data["utterances_histories"]
    candidate_topics_batch = []
    for utter_sentences in utter_sentences_batch:
        try:
            topic_ranked_list = get_ranked_list(utter_sentences, responses)
            candidate_topics = [topic2response[responses[i]] for i in topic_ranked_list[:TOP_K]]
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
