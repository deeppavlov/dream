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


@app.route("/is_command_valid", methods=["POST"])
def respond_is_command_valid():
    st_time = time.time()
    command = request.json.get("command", None)
    # dialog_id = request.json.get("dialog_id", None)
    if "forward" in command:
        results = {"result": False}
    else:
        results = {"result": True}

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

    total_time = time.time() - st_time
    logger.info(f"fake-robot-server `is_command_performed` exec time: {total_time:.3f}s")
    return jsonify(results)
