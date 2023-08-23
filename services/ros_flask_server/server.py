import threading
import rospy

from std_msgs.msg import String
from flask import Flask, request
from flask import jsonify

import logging
import time
from os import getenv

import sentry_sdk


sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

talker = rospy.Publisher("talker", String, queue_size=1)

threading.Thread(target=lambda: rospy.init_node("listener", disable_signals=True)).start()

VALID_COMMANDS = ["test_command"]
COMMAND_QUEUE = []
EXECUTING_COMMAND = None


@app.route("/ping", methods=["POST"])
def ping():
    return "pong"


@app.route("/set_commands", methods=["POST"])  # this endpoint should not be accessed from within dream
def respond_set_commands():
    global VALID_COMMANDS

    st_time = time.perf_counter()
    VALID_COMMANDS = list(map(lambda i: i.lower(), request.json.get("commands", [])))
    if not VALID_COMMANDS:
        logger.info("embodied-server user did not send valid commands list")
    logger.info(f"embodied-server `VALID_COMMANDS` set: {VALID_COMMANDS}")

    total_time = time.perf_counter() - st_time

    logger.info(f"embodied-server `is_command_valid` exec time: {total_time:.3f}s")

    return {"result": bool(VALID_COMMANDS)}


@app.route("/is_command_valid", methods=["POST"])
def respond_is_command_valid():
    st_time = time.perf_counter()

    command = request.json.get("command", None)
    results = {"result": any(item in command for item in VALID_COMMANDS)}
    logger.info(f"embodied-server `is_command_valid` results: {results}")

    total_time = time.perf_counter() - st_time

    logger.info(f"embodied-server `is_command_valid` exec time: {total_time:.3f}s")

    return jsonify(results)


@app.route("/perform_command", methods=["POST"])
def respond_perform_command():
    st_time = time.perf_counter()

    command = request.json.get("command", None)
    cmd_valid = command in VALID_COMMANDS
    logger.info(f"ros-flask-server received command: {command}, valid? -{cmd_valid}")
    if cmd_valid:
        logger.info("Sending command to ROS...")
        try:
            talker.publish(command)
            logger.info("Successfully returned from ROS!")
            COMMAND_QUEUE.append(command)
        except Exception as e:
            logger.info(f"Error inside ROS: {e}")
    results = {"result": cmd_valid}
    logger.info(f"embodied-server `perform_command` {command} appended to queue?: {results}")

    total_time = time.perf_counter() - st_time

    logger.info(f"embodied-server `perform_command` exec time: {total_time:.3f}s")

    return jsonify(results)


@app.route("/receive_command", methods=["POST"])  # this endpoint should not be accessed from within dream
def respond_receive_command():
    global EXECUTING_COMMAND

    st_time = time.perf_counter()

    command = COMMAND_QUEUE.pop(0) if COMMAND_QUEUE else None
    results = {"command": command}
    logger.info(f"embodied-server `receive_command` results: {results}")

    total_time = time.perf_counter() - st_time

    logger.info(f"embodied-server `receive_command` exec time: {total_time:.3f}s")

    return jsonify(results)


@app.route("/is_command_performed", methods=["POST"])
def respond_is_command_performed():
    st_time = time.perf_counter()

    results = {"result": EXECUTING_COMMAND}
    logger.info(f"embodied-server `is_command_performed` results: {results}")

    total_time = time.perf_counter() - st_time

    logger.info(f"embodied-server `is_command_performed` exec time: {total_time:.3f}s")

    return jsonify(results)


@app.route("/command_is_performed", methods=["POST"])  # this endpoint should not be accessed from within dream
def respond_command_is_performed():
    global EXECUTING_COMMAND

    st_time = time.perf_counter()

    results = {"result": True}
    logger.info(f"embodied-server `command_is_performed` results: {results}")
    EXECUTING_COMMAND = None

    total_time = time.perf_counter() - st_time

    logger.info(f"embodied-server `command_is_performed` exec time: {total_time:.3f}s")

    return jsonify(results)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6000, debug=True)
