import logging
import time
from os import getenv

import sentry_sdk

from flask import Flask, request, jsonify


sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

VALID_COMMANDS = [
    "track_object",
    "turn_counterclockwise",
    "turn_clockwise",
    "move_forward",
    "move_backward",
    "open_door",
    "move_to_point",
]


@app.route("/ping", methods=["POST"])
def ping():
    return "pong"


@app.route("/is_command_valid", methods=["POST"])
def respond_is_command_valid():
    st_time = time.time()
    command = request.json.get("command", None)
    # dialog_id = request.json.get("dialog_id", None)
    if any([name in command for name in VALID_COMMANDS]):
        results = {"result": True}
    else:
        results = {"result": False}
    logger.info(f"fake-robot-server `is_command_valid` results: {results}")

    total_time = time.time() - st_time
    logger.info(f"fake-robot-server `is_command_valid` exec time: {total_time:.3f}s")
    return jsonify(results)


@app.route("/perform_command", methods=["POST"])
def respond_perform_command():
    st_time = time.time()
    command = request.json.get("command", None)
    # dialog_id = request.json.get("dialog_id", None)
    if "forward" in command:
        results = {"result": False}
    else:
        results = {"result": True}
    logger.info(f"fake-robot-server `perform_command` results: {results}")

    total_time = time.time() - st_time
    logger.info(f"fake-robot-server `perform_command` exec time: {total_time:.3f}s")
    return jsonify(results)


@app.route("/is_command_performed", methods=["POST"])
def respond_is_command_performed():
    st_time = time.time()
    command = request.json.get("command", None)
    # dialog_id = request.json.get("dialog_id", None)
    if "forward" in command:
        results = {"result": False}
    else:
        results = {"result": True}
    logger.info(f"fake-robot-server `is_command_performed` results: {results}")

    total_time = time.time() - st_time
    logger.info(f"fake-robot-server `is_command_performed` exec time: {total_time:.3f}s")
    return jsonify(results)
