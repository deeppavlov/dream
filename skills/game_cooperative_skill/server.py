#!/usr/bin/env python

import logging
import time
from os import getenv
import random
import pathlib
import datetime
import copy
import difflib

from flask import Flask, request, jsonify
from healthcheck import HealthCheck
import sentry_sdk
from sentry_sdk.integrations.logging import ignore_logger

from common.constants import CAN_NOT_CONTINUE, CAN_CONTINUE_SCENARIO, MUST_CONTINUE
from common.universal_templates import is_switch_topic, if_chat_about_particular_topic

from common.utils import get_skill_outputs_from_dialog, is_yes
from common.game_cooperative_skill import game_skill_was_proposed, GAMES_COMPILED_PATTERN, FALLBACK_ACKN_TEXT
from common.gaming import find_games_in_text
from common.dialogflow_framework.programy.text_preprocessing import clean_text

from router import run_skills as skill


ignore_logger("root")

sentry_sdk.init(getenv("SENTRY_DSN"))
DB_FILE = pathlib.Path(getenv("DB_FILE", "/data/game-cooperative-skill/game_db.json"))
MEMORY_LENGTH = 3

logging.basicConfig(format="%(asctime)s - %(pathname)s - %(lineno)d - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
health = HealthCheck(app, "/healthcheck")
logging.getLogger("werkzeug").setLevel("WARNING")


# add your own check function to the healthcheck
def db_is_updated():
    curr_date = datetime.datetime.now()
    min_update_time = datetime.timedelta(hours=25)
    if DB_FILE.exists():
        file_modification_time = datetime.datetime.fromtimestamp(DB_FILE.lstat().st_mtime)
        data_is_expired = curr_date - min_update_time > file_modification_time
        msg = "db is expired" if data_is_expired else "db is updated"
        msg += f", last modified date of db is {file_modification_time.strftime('%m/%d/%Y, %H:%M:%S')}"
        if data_is_expired:
            sentry_sdk.capture_message(msg)
        return True, msg
    else:
        msg = "db file is not created"
        logger.error(msg)
        sentry_sdk.capture_message(msg)
        return False, msg


health.add_check(db_is_updated)


def get_agent_intents(last_utter):
    annotations = last_utter.get("annotations", {})
    agent_intents = {}
    for intent_name, intent_detector in annotations.get("intent_catcher", {}).items():
        if intent_detector.get("detected", 0) == 1:
            agent_intents[intent_name] = True

    if not agent_intents.get("topic_switching") and (
        is_switch_topic(last_utter)
        or agent_intents.get("exit")
        or agent_intents.get("stupid")
        or agent_intents.get("cant_do")
        or agent_intents.get("tell_me_a_story")
        or agent_intents.get("weather_forecast_intent")
        or agent_intents.get("what_can_you_do")
        or agent_intents.get("what_is_your_job")
        or agent_intents.get("what_is_your_name")
        or agent_intents.get("what_time")
    ):
        agent_intents["topic_switching"] = True
    return agent_intents


@app.route("/respond", methods=["POST"])
def respond():
    dialogs_batch = [None]
    st_time = time.time()
    dialogs_batch = request.json["dialogs"]
    rand_seed = request.json.get("rand_seed")

    responses = []
    for dialog in dialogs_batch:
        prev_skill_outputs = get_skill_outputs_from_dialog(
            dialog["utterances"][-MEMORY_LENGTH:], "game_cooperative_skill", activated=True
        )
        is_active_last_answer = bool(prev_skill_outputs)
        human_attr = dialog["human"]["attributes"]
        prev_state = human_attr.get("game_cooperative_skill", {}).get("state", {})
        try:
            state = copy.deepcopy(prev_state)
            if state and not is_active_last_answer:
                state["messages"] = []
            # pre_len = len(state.get("messages", []))

            last_utter = dialog["human_utterances"][-1]

            last_utter_text = last_utter["text"].lower()
            agent_intents = get_agent_intents(last_utter)

            # for tests
            attr = {}
            if rand_seed:
                random.seed(int(rand_seed))
            response, state = skill([last_utter_text], state, agent_intents)

            # logger.info(f"state = {state}")
            # logger.info(f"last_utter_text = {last_utter_text}")
            # logger.info(f"response = {response}")
            bot_utterance = dialog["bot_utterances"][-1] if dialog["bot_utterances"] else {}
            text = response.get("text", "Sorry")
            if not response.get("confidence"):
                confidence = 0
            elif not is_active_last_answer and if_chat_about_particular_topic(
                dialog["human_utterances"][-1],
                bot_utterance,
                compiled_pattern=GAMES_COMPILED_PATTERN,
            ) and find_games_in_text(last_utter_text):
                confidence = 0
            elif not is_active_last_answer and if_chat_about_particular_topic(
                dialog["human_utterances"][-1],
                bot_utterance,
                compiled_pattern=GAMES_COMPILED_PATTERN,
            ):
                confidence = 1
            elif is_active_last_answer:
                confidence = 1
            elif is_yes(dialog["human_utterances"][-1]) and game_skill_was_proposed(bot_utterance):
                confidence = 1
            elif not is_yes(dialog["human_utterances"][-1]) and game_skill_was_proposed(bot_utterance):
                confidence = 0.95
                text = FALLBACK_ACKN_TEXT
                state = prev_state
            elif GAMES_COMPILED_PATTERN.search(last_utter_text) and not is_active_last_answer:
                confidence = 0.98
            else:
                confidence = 0

            curr_text = clean_text(text.lower())
            last_text = clean_text(bot_utterance.get("text", "").lower())
            ratio = difflib.SequenceMatcher(None, curr_text.split(), last_text.split()).ratio()

            if ratio > 0.95:
                confidence = 0

            if confidence == 1:
                can_continue = MUST_CONTINUE
            elif confidence > 0.95:
                can_continue = CAN_CONTINUE_SCENARIO
            else:
                can_continue = CAN_NOT_CONTINUE

            human_attr["game_cooperative_skill"] = {"state": state}
            attr["can_continue"] = can_continue

        except Exception as exc:
            sentry_sdk.capture_exception(exc)
            logger.exception(exc)
            text = ""
            confidence = 0.0
            human_attr["game_cooperative_skill"] = {"state": prev_state}
            attr = {}

        bot_attr = {}
        responses.append((text, confidence, human_attr, bot_attr, attr))

        total_time = time.time() - st_time
        logger.info(f"game_cooperative_skill exec time = {total_time:.3f}s")

    return jsonify(responses)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
