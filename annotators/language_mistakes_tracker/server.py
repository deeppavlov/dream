import logging
import json
import os
import time
from common.language_mistakes_tracker import LanguageMistakes

from healthcheck import HealthCheck
from flask import Flask, jsonify, request


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
health = HealthCheck(app, "/healthcheck")


def update_mistakes_state(requested_data):
    results = []
    st_time = time.time()
    dialog = requested_data["dialog"]
    logger.info(f"dialog: {dialog}")
    # for filename in os.listdir("../skills/dff_language_practice_skill/data"):
    #     f = os.path.join("../skills/dff_language_practice_skill/data", filename)
    #     if os.path.isfile(f):
    #         scenario = json.load(open(f))
    if dialog["bot_utterances"] != []:
        prev_active_skill = dialog["bot_utterances"][-1]["active_skill"]
        scenarios_descriptions = dialog["human_utterances"][-1]["user"]["attributes"]["scenarios_descriptions"]
        user_utterances = dialog["human_utterances"][-1]["user"]["attributes"]["user_utterances"]
    else:
        prev_active_skill = None
        scenarios_descriptions = {}
        user_utterances = []
        for filename in os.listdir("data"):
            f = os.path.join("data", filename)
            if os.path.isfile(f):
                scenario = json.load(open(f))
                scenarios_descriptions[filename.replace(".json", "")] = scenario["situation_description"]

    not2review_skills = ["dff_mistakes_review_skill", "dff_friendship_skill"]
    if prev_active_skill in not2review_skills:
        mistakes_state = None
        tracker = LanguageMistakes(initial_state=mistakes_state)
    else:
        try:
            mistakes_state = dialog["human"]["attributes"]["language_mistakes"]
        except:
            mistakes_state = None
        tracker = LanguageMistakes(initial_state=mistakes_state)
        tracker.update_language_mistakes_tracker(dialog)
        user_uttr = dialog["human_utterances"][-1]["text"]
        user_utterances.append(user_uttr)

    new_state = tracker.dump_state()
    results.append(
        {
            "human_attributes": {
                "language_mistakes": new_state,
                "scenarios_descriptions": scenarios_descriptions,
                "user_utterances": user_utterances,
            }
        }
    )
    total_time = time.time() - st_time
    logger.info(f"language_mistakes exec time: {total_time:.3f}s")
    logger.info(f"language_mistakes state: {new_state}")
    return results


@app.route("/respond", methods=["POST"])
def respond():
    responses = update_mistakes_state(request.json)
    return jsonify(responses)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
