import json
import logging
import time
from os import getenv

import requests
import sentry_sdk
from flask import Flask, request, jsonify


sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

ROS_FSM_SERVER = getenv("ROS_FSM_SERVER")
ROS_FSM_STATUS_ENDPOINT = f"{ROS_FSM_SERVER}/robot_status"
ROS_FSM_INTENT_ENDPOINT = f"{ROS_FSM_SERVER}/upload_response"


@app.route("/send", methods=["POST"])
def respond():
    st_time = time.time()
    annotated_bot_utterances = request.json.get("annotated_bot_utterances", [])
    for ann_uttr in annotated_bot_utterances:
        command = ann_uttr.get("attributes", {}).get("robot_command")
        if command:
            logger.info(f"robot_command_sender: sending to robot:\n{command}")
            requests.post(ROS_FSM_INTENT_ENDPOINT, data=json.dumps({"text": command}))
        else:
            logger.info(f"robot_command_sender was called but NO command found in annotated_bot_utterance: "
                        f"{ann_uttr}")

    total_time = time.time() - st_time
    logger.info(f"robot_command_sender exec time: {total_time:.3f}s")
    return jsonify(["Command sent"] * len(annotated_bot_utterances))
