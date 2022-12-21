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
            logger.info(f"robot_command_sender: command `{command}` is being sent to robot")
            result = False
            try:
                result = send_robot_command_to_perform(command, ROS_FSM_SERVER, dialog_id)
            except Exception as e:
                sentry_sdk.capture_exception(e)
                logger.exception(e)

            if result:
                results += [{"human_attributes": {"performing_command": command}}]
            else:
                results += [{"human_attributes": {}}]
            logger.info(f"robot_command_sender: status of sending command `{command}`: `{result}`")
        else:
            logger.info("robot_command_sender: NO command found in prev bot uttr")
            results += [{"human_attributes": {}}]

    total_time = time.time() - st_time
    logger.info(f"robot_command_sender exec time: {total_time:.3f}s")
    return jsonify(results)
