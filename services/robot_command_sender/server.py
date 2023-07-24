import logging
import time
from os import getenv

import sentry_sdk
from common.robot import send_robot_command_to_perform
from flask import Flask, request, jsonify


sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

ROS_FSM_SERVER = getenv("ROS_FSM_SERVER")
SKILL_NAMES_SENDING_COMMANDS = ["intent_responder", "dff_intent_responder_skill"]


@app.route("/send", methods=["POST"])
def respond():
    st_time = time.time()
    results = []
    ann_human_utterances = request.json.get("last_human_utterances", [])
    ann_bot_utterances = request.json.get("bot_utterances", [])
    dialog_ids = request.json.get("dialog_ids", [])

    for ann_human_uttr, ann_bot_uttr, dialog_id in zip(ann_human_utterances, ann_bot_utterances, dialog_ids):
        active_skill = ann_bot_uttr.get("active_skill", {})
        hyps = ann_human_uttr.get("hypotheses", [])
        current_skill_hyp = [hyp for hyp in hyps if hyp.get("skill_name", "") == active_skill][0]
        command = current_skill_hyp.get("command_to_perform", "")
        if active_skill in SKILL_NAMES_SENDING_COMMANDS and len(command):
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
