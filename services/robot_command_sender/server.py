import json
import logging
from os import getenv
from typing import Dict

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
def respond(annotated_bot_utterance: Dict):

    command = annotated_bot_utterance.get("attributes", {}).get("robot_command")
    if command:
        logger.info(f"robot_command_sender: sending to robot:\n{command}")
        requests.post(ROS_FSM_INTENT_ENDPOINT, data=json.dumps({"text": command}))
    else:
        logger.info(f"robot_command_sender was called but NO command found in annotated_bot_utterance: "
                    f"{annotated_bot_utterance}")
