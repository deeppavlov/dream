import logging
import time
import os

from flask import Flask, request, jsonify
import sentry_sdk

from convert import get_ranked_list

sentry_sdk.init(os.getenv("SENTRY_DSN"))


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
logging.getLogger("werkzeug").setLevel("WARNING")

app = Flask(__name__)

TOP_K = 3

topic2response = {
    "Let's chat about food": "dff_food_skill",
    "Let's chat about books": "book_skill",
    "Let's chat about sport": "dff_sport_skill",
    "Let's chat about movies": "dff_movie_skill",
    "Let's chat about animals": "dff_animals_skill",
    "Let's chat about games": "game_cooperative_skill",
    "Let's chat about music": "dff_music_skill",
    "Let's chat about news": "news_api_skill",
    "Let's chat about travels": "dff_travel_skill",
}

responses = list(topic2response.keys())


def recommend_according_to_age(human_attr):
    skills_to_recommend = []
    if human_attr.get("age_group", "unknown") != "unknown":
        if human_attr["age_group"] == "kid":
            skills_to_recommend = [
                "game_cooperative_skill",
                "dff_animals_skill",
                "dff_food_skill",
                # "small_talk_skill:superheroes",
                # "small_talk_skill:school"
            ]

    return skills_to_recommend


def handler(requested_data):
    st_time = time.time()

    utter_sentences_batch = requested_data["utterances_histories"]
    human_attributes_batch = requested_data["human_attributes"]

    candidate_topics_batch = []
    for utter_sentences, human_attr in zip(utter_sentences_batch, human_attributes_batch):
        try:
            topic_ranked_list = get_ranked_list(utter_sentences, responses)
            candidate_topics = [topic2response[responses[i]] for i in topic_ranked_list[:TOP_K]]
            age_group_skills = recommend_according_to_age(human_attr)

            candidate_topics_batch.append(age_group_skills if age_group_skills else candidate_topics)
        except Exception as exc:
            logger.exception(exc)
            sentry_sdk.capture_exception(exc)
            candidate_topics_batch.append([])

    total_time = time.time() - st_time
    logger.warning(f"topic_recommendation exec time: {total_time:.3f}s")
    # logger.warning(candidate_topics_batch)
    return candidate_topics_batch


try:
    request_data = {
        "utterances_histories": [
            [
                "i like to have conversation",
                "Hi, this is an Alexa Prize Socialbot! I think we have not met yet. What name would you like "
                "me to call you?",
                "boss bitch",
                "I'm so clever that sometimes I don't understand a single word of what i'm saying.",
                "how is that",
                "Hmm. If you would like to talk about something else just say, 'lets talk about something else'.",
                "you pick the topic of conversation",
            ]
        ],
        "personality": [{}],
        "num_ongoing_utt": [0],
        "human_attributes": [
            {"age_group": "unknown"}
        ]
    }
    handler(request_data)
    logger.warning("test query processed")
except Exception as exc:
    sentry_sdk.capture_exception(exc)
    logger.exception(exc)
    raise exc

logger.warning(f"topic_recommendation is loaded and ready")


@app.route("/respond", methods=["POST"])
def respond():
    response = handler(request.json)
    return jsonify(response)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
