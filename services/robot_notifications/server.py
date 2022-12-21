import logging
import time
from os import getenv

import sentry_sdk

from common.robot import check_if_command_performed
from flask import Flask, request, jsonify


sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

ROS_FSM_SERVER = getenv("ROS_FSM_SERVER")
SERVICE_PORT = int(getenv("SERVICE_PORT"))


@app.route("/check", methods=["POST"])
def respond():
    st_time = time.time()
    results = []
    dialogs = request.json.get("dialogs", [])
    dialog_ids = request.json.get("dialog_ids", [])

    for dialog, dialog_id in zip(dialogs, dialog_ids):
        command = dialog["human"]["attributes"].get("performing_command")

        if command:
            logger.info(f"robot_notifications: found command `{command}` sent to robot")
            result = False
            try:
                result = check_if_command_performed(command, ROS_FSM_SERVER, dialog_id)
            except Exception as e:
                sentry_sdk.capture_exception(e)
                logger.exception(e)
            if result:
                # command was completed, so remove it from human attributes
                results += [{"human_attributes": {"performing_command": None}}]
            else:
                # command is not completed, so keep it in human attributes
                results += [{"human_attributes": {"performing_command": command}}]
            logger.info(f"robot_notifications: status of command `{command}` performance: `{result}`")
        else:
            logger.info("robot_notifications: NO command found in human attributes")
            results += [{}]

    total_time = time.time() - st_time
    logger.info(f"robot_notifications exec time: {total_time:.3f}s")
    return jsonify(results)
