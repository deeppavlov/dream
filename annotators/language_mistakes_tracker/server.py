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
    try:
        mistakes_state = dialog["human"]["attributes"]["language_mistakes"]
    except:
        mistakes_state = None

    tracker = LanguageMistakes(initial_state=mistakes_state)
    tracker.update_language_mistakes_tracker(dialog)
    new_state = tracker.dump_state()
    results.append({"human_attributes": {"language_mistakes": new_state}})
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

