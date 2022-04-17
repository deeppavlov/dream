import logging
import json
import os
import time
import re
from common.goal_state_tracker import GoalTracker


# import sentry_sdk
from healthcheck import HealthCheck
from flask import Flask, jsonify, request

# sentry_sdk.init(os.getenv("SENTRY_DSN")) эта штука всегда и везде не работает, потому что SENTRY_DSN не прописан

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
health = HealthCheck(app, "/healthcheck")

tracker = GoalTracker()


def update_goals_state(requested_data):
    results = []
    st_time = time.time()
    detected_goals = requested_data["last_detected_goals"]
    tracker.load_state(requested_data["goals_tracker_state"])
    prev_skill_goal_status = requested_data["skill_goal_status"]
    active_skill = requested_data["last_active_skill"]
    tracker.update_human_goals_from_bot(prev_skill_goal_status, active_skill)
    tracker.update_human_goals(detected_goals)
    results.append({"human_attributes": {"goals_tracker": tracker.save_state()}})
    total_time = time.time() - st_time
    logger.info(f"human_goals exec time: {total_time:.3f}s")
    return results


@app.route("/respond", methods=["POST"])
def respond():
    responses = update_goals_state(request.json)
    return jsonify(responses)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)

