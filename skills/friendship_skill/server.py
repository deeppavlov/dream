#!/usr/bin/env python

import logging
import time
import os
import random

from flask import Flask, request, jsonify
from healthcheck import HealthCheck
import sentry_sdk
from sentry_sdk.integrations.logging import ignore_logger


from common.constants import CAN_NOT_CONTINUE, CAN_CONTINUE

import dialog_flows.main as main_dialog_flow
import dialog_flows.utils as dialog_utils
import dialog_flows.condition_utils as condition_utils
import common.greeting as common_greeting


ignore_logger("root")

sentry_sdk.init(os.getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(pathname)s - %(lineno)d - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


dialog_flow = main_dialog_flow.composite_dialog_flow

app = Flask(__name__)
health = HealthCheck(app, "/healthcheck")

logger.info("friendship_skill is loaded and ready")


def load_into_dialog_flow(human_utter_index, dialog, state, entities):
    dialog_flow.reset()
    dialog_flow_state = state.get("dialog_flow_state")
    if dialog_flow_state:
        dialog_flow.deserialize(dialog_flow_state)
    agent = {
        "last_human_utter_index": state.get("last_human_utter_index", -1),
        "human_utter_index": human_utter_index,
        "dialog": dialog,
        "entities": entities,
        "shared_memory": state.get("shared_memory", {}),
        "history": state.get("history", {}),
        "used_links": state.get("used_links", {}),
    }
    dialog_flow.controller().vars()["agent"] = agent


def get_dialog_state(dialog_flow):
    agent = dialog_flow.controller().vars()["agent"]
    human_utter_index = agent["human_utter_index"]
    history = agent["history"]
    used_links = agent["used_links"]
    history[str(human_utter_index)] = dialog_flow.controller().vars()["__system_state__"]
    state = {
        "shared_memory": agent["shared_memory"],
        "last_human_utter_index": human_utter_index,
        "history": history,
        "used_links": used_links,
    }
    del dialog_flow.controller().vars()["agent"]
    state["dialog_flow_state"] = dialog_flow.serialize()
    logger.debug(f"state={state}")
    return state


@app.route("/respond", methods=["POST"])
def respond():
    # next commented line for test creating
    # import pathlib;import json;json.dump(request.json,pathlib.Path("tests/create_update_in.json").open("wt"),indent=4)
    st_time = time.time()
    dialog_batch = request.json.get("dialog_batch", [])
    human_utter_index_batch = request.json.get("human_utter_index_batch", [0] * len(dialog_batch))
    friendship_skill_state_batch = request.json.get("friendship_skill_state_batch", [{}] * len(dialog_batch))
    entities_batch = request.json.get("entities_batch", [{}] * len(dialog_batch))
    rand_seed = request.json.get("rand_seed")  # for tests

    responses = []
    for human_utter_index, dialog, state, entities in zip(
        human_utter_index_batch, dialog_batch, friendship_skill_state_batch, entities_batch
    ):
        try:
            # for tests
            logger.debug(entities)
            if rand_seed:
                random.seed(int(rand_seed))

            load_into_dialog_flow(human_utter_index, dialog, state, entities)

            # run turn
            dialog_flow.user_turn(dialog["human_utterances"][-1]["text"])
            text = dialog_flow.system_turn()
            if human_utter_index > 9 or ("Sorry" in text and len(text) < 15):
                confidence = 0
            elif condition_utils.is_first_our_response(dialog_flow.controller().vars()):
                confidence = dialog_utils.DIALOG_BEGINNING_START_CONFIDENCE
            elif not condition_utils.is_interrupted(
                dialog_flow.controller().vars()
            ) and common_greeting.dont_tell_you_answer(
                dialog_utils.get_last_user_utterance(dialog_flow.controller().vars())
            ):
                confidence = dialog_utils.DIALOG_BEGINNING_SHORT_ANSWER_CONFIDENCE
            elif not condition_utils.is_interrupted(dialog_flow.controller().vars()):
                confidence = dialog_utils.DIALOG_BEGINNING_CONTINUE_CONFIDENCE
            else:
                confidence = dialog_utils.MIDDLE_DIALOG_START_CONFIDENCE

            # dialog_flow save state
            state = get_dialog_state(dialog_flow)

            can_continue = CAN_CONTINUE if confidence else CAN_NOT_CONTINUE
            human_attr = {"friendship_skill_state": state}
            hype_attr = {"can_continue": can_continue}

            responses.append((text, confidence, human_attr, {}, hype_attr))
        except Exception as exc:
            sentry_sdk.capture_exception(exc)
            logger.exception(exc)
            responses.append(("Sorry", 0.0, {}))

        total_time = time.time() - st_time
        logger.info(f"friendship_skill exec time = {total_time:.3f}s")

    # next commented line for test creating
    # import pathlib;import json;json.dump(responses, pathlib.Path("tests/create_update_out.json").open("wt"), indent=4)
    return jsonify(responses)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
