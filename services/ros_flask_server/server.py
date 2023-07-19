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

VALID_COMMANDS = []
COMMAND_QUEUE = []
EXECUTING_COMMAND = None

# WARNING: naive implementation: only 1 client supported


@app.route("/set_commands", methods=["POST"])  # this endpoint should not be accessed from within dream
def respond_set_commands():
    global VALID_COMMANDS

    st_time = time.perf_counter()
    VALID_COMMANDS = list(map(lambda i: i.lower(), request.json.get("commands", [])))
    if not VALID_COMMANDS:
        logger.info("mint-server user did not send valid commands list," + "resetting to default")
    logger.info(f"mint-server `VALID_COMMANDS` set: {VALID_COMMANDS}")

    total_time = time.perf_counter() - st_time

    logger.info(f"mint-server `is_command_valid` exec time: {total_time:.3f}s")

    return {"result": True}


@app.route("/is_command_valid", methods=["POST"])
def respond_is_command_valid():
    st_time = time.perf_counter()

    command = request.json.get("command", None)
    results = {"result": any(item in command for item in VALID_COMMANDS)}
    logger.info(f"mint-server `is_command_valid` results: {results}")

    total_time = time.perf_counter() - st_time

    logger.info(f"mint-server `is_command_valid` exec time: {total_time:.3f}s")

    return jsonify(results)


@app.route("/perform_command", methods=["POST"])
def respond_perform_command():
    st_time = time.perf_counter()

    command = request.json.get("command", None)
    logger.info("Sending command to ROS...")
    talker.publish(command)
    logger.info("Successfully returned from ROS!")
    results = {"result": command in VALID_COMMANDS}
    COMMAND_QUEUE.append(command)
    logger.info(f"mint-server `perform_command` {command} appended to queue?: {results}")

    total_time = time.perf_counter() - st_time

    logger.info(f"mint-server `perform_command` exec time: {total_time:.3f}s")

    return jsonify(results)


@app.route("/recieve_command", methods=["POST"])  # this endpoint should not be accessed from within dream
def respond_recieve_command():
    global EXECUTING_COMMAND

    st_time = time.perf_counter()

    command = COMMAND_QUEUE.pop(0) if COMMAND_QUEUE else None
    results = {"command": command}
    logger.info(f"mint-server `recieve_command` results: {results}")

    total_time = time.perf_counter() - st_time

    logger.info(f"mint-server `recieve_command` exec time: {total_time:.3f}s")

    return jsonify(results)


@app.route("/is_command_performed", methods=["POST"])
def respond_is_command_performed():
    st_time = time.perf_counter()

    results = {"result": EXECUTING_COMMAND}
    logger.info(f"mint-server `is_command_performed` results: {results}")

    total_time = time.perf_counter() - st_time

    logger.info(f"mint-server `is_command_performed` exec time: {total_time:.3f}s")

    return jsonify(results)


@app.route("/command_is_performed", methods=["POST"])  # this endpoint should not be accessed from within dream
def respond_command_is_performed():
    global EXECUTING_COMMAND

    st_time = time.perf_counter()

    results = {"result": True}
    logger.info(f"mint-server `command_is_performed` results: {results}")
    EXECUTING_COMMAND = None

    total_time = time.perf_counter() - st_time

    logger.info(f"mint-server `command_is_performed` exec time: {total_time:.3f}s")

    return jsonify(results)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
