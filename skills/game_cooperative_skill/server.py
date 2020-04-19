#!/usr/bin/env python

import logging
import time
from os import getenv
import random

from flask import Flask, request, jsonify
import sentry_sdk

from common.constants import CAN_NOT_CONTINUE, CAN_CONTINUE
from common.universal_templates import is_switch_topic
from common.utils import get_skill_outputs_from_dialog
from router import run_skills as skill

sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    dialogs_batch = request.json["dialogs"]
    rand_seed = request.json.get("rand_seed")
    # for tests
    if rand_seed:
        random.seed(int(rand_seed))
    responses = []

    for dialog in dialogs_batch:
        prev_news_outputs = get_skill_outputs_from_dialog(
            dialog["utterances"], "game_cooperative_skill", activated=True
        )
        prev_news_output = prev_news_outputs[-1] if len(prev_news_outputs) > 0 else {}
        state = prev_news_output.get("state", {})

        last_utter = dialog["human_utterances"][-1]

        last_utter_text = last_utter["text"].lower()
        agent_intents = {"switch_topic_intent": True} if is_switch_topic(last_utter) else {}
        response, state = skill([last_utter_text], state, agent_intents)

        logger.info(f"state = {state}")
        logger.info(f"last_utter_text = {last_utter_text}")
        logger.info(f"response = {response}")
        text = response.get("text", "Sorry")
        confidence = 1.0 if response.get("confidence") else 0.0
        confidence *= 0.8 if "I like to talk about games." in response.get("text") else 1.0

        can_continue = CAN_CONTINUE if confidence else CAN_NOT_CONTINUE
        attr = {"can_continue": can_continue, "state": state}
        responses.append((text, confidence, attr))

    total_time = time.time() - st_time
    logger.info(f"game_cooperative_skill exec time = {total_time:.3f}s")
    return jsonify(responses)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
