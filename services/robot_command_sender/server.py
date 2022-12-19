import json
import logging
import time
from os import getenv

import requests
import sentry_sdk

from common.robot import send_robot_command_to_perform
from flask import Flask, request, jsonify


sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

ROS_FSM_SERVER = getenv("ROS_FSM_SERVER")


@app.route("/send", methods=["POST"])
def respond():
    st_time = time.time()
    results = []
    annotated_bot_utterances = request.json.get("annotated_bot_utterances", [])
    dialog_ids = request.json.get("dialog_ids", [])

    for ann_uttr, dialog_id in zip(annotated_bot_utterances, dialog_ids):
        command = ann_uttr.get("attributes", {}).get("robot_command")
        if command:
            logger.info(f"robot_command_sender: sending to robot:\n{command}")
            try:
                result = send_robot_command_to_perform(command, ROS_FSM_SERVER, dialog_id)
                result = "Sent" if result else "Failed"
            except Exception as e:
                sentry_sdk.capture_exception(e)
                logger.exception(e)
                result = "Failed"

            results += [result]
            logger.info(f"robot_command_sender: status of sending:\n{result}")
        else:
            logger.info(
                f"robot_command_sender: NO command found in annotated_bot_utterance: " f"{ann_uttr}"
            )
            results += ["Failed"]

    total_time = time.time() - st_time
    logger.info(f"robot_command_sender exec time: {total_time:.3f}s")
    return jsonify(results)
