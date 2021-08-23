#!/usr/bin/env python

import json
import logging
import time
import os
import random

import sentry_sdk
from dff import Context
from flask import Flask, request, jsonify
from healthcheck import HealthCheck
from sentry_sdk.integrations.logging import ignore_logger

import common.constants as common_constants
import common.dialogflow_framework.utils.dialogflow as dialogflow_utils
import common.dialogflow_framework.programy.text_preprocessing as text_utils
import test_server
from dialogflows.main import actor

ignore_logger("root")

sentry_sdk.init(os.getenv("SENTRY_DSN"))
SERVICE_NAME = os.getenv("SERVICE_NAME")
SERVICE_PORT = int(os.getenv("SERVICE_PORT"))
RANDOM_SEED = int(os.getenv("RANDOM_SEED", 2718))

logging.basicConfig(format="%(asctime)s - %(pathname)s - %(lineno)d - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)


app = Flask(__name__)
health = HealthCheck(app, "/healthcheck")
logging.getLogger("werkzeug").setLevel("WARNING")


def handler(requested_data, random_seed=None):
    st_time = time.time()
    dialog_batch = requested_data.get("dialog_batch", [])
    human_utter_index_batch = requested_data.get("human_utter_index_batch", [0] * len(dialog_batch))
    state_batch = requested_data.get(f"{SERVICE_NAME}_state_batch", [{}] * len(dialog_batch))
    ctx_batch = requested_data.get(f"{SERVICE_NAME}_ctx_batch", [{}] * len(dialog_batch))
    dff_shared_state_batch = requested_data.get(f"dff_shared_state_batch", [{}] * len(dialog_batch))
    entities_batch = requested_data.get("entities_batch", [{}] * len(dialog_batch))
    used_links_batch = requested_data.get("used_links_batch", [{}] * len(dialog_batch))
    age_group_batch = requested_data.get("age_group_batch", [""] * len(dialog_batch))
    disliked_skills_batch = requested_data.get("disliked_skills_batch", [{}] * len(dialog_batch))
    clarification_request_flag_batch = requested_data.get(
        "clarification_request_flag_batch", [False] * len(dialog_batch)
    )
    random_seed = requested_data.get("random_seed", random_seed)  # for tests

    responses = []
    for (
        human_utter_index,
        dialog,
        state,
        ctx,
        dff_shared_state,
        entities,
        used_links,
        age_group,
        disliked_skills,
        clarification_request_flag,
    ) in zip(
        human_utter_index_batch,
        dialog_batch,
        state_batch,
        ctx_batch,
        dff_shared_state_batch,
        entities_batch,
        used_links_batch,
        age_group_batch,
        disliked_skills_batch,
        clarification_request_flag_batch,
    ):
        try:
            # for tests
            if random_seed:
                random.seed(int(random_seed))

            text = dialog["human_utterances"][-1]["text"]
            text = text_utils.clean_text(text)

            agent = dialogflow_utils.load_into_dialogflow(
                human_utter_index,
                dialog,
                state,
                dff_shared_state,
                entities,
                used_links,
                age_group,
                disliked_skills,
                clarification_request_flag,
            )

            if ctx:
                ctx = Context.parse_obj(ctx)
            else:
                ctx = Context()
            ctx.add_human_utterance(text)
            shared_memory = ctx.shared_memory
            shared_memory["vars"] = {"agent": agent}
            ctx.shared_memory = shared_memory
            ctx = actor(ctx)
            text = ctx.actor_text_response
            vars = ctx.shared_memory.get("vars", {})
            confidence = ctx.shared_memory.get("confidence", 1.0)
            can_continue = ctx.shared_memory.get("continue_flag", common_constants.CAN_CONTINUE_SCENARIO)
            (
                state,
                dff_shared_state,
                used_links,
                age_group,
                disliked_skills,
                response_parts,
            ) = dialogflow_utils.get_dialog_state(vars)

            human_attr = {
                f"{SERVICE_NAME}_state": state,
                f"{SERVICE_NAME}_ctx": json.loads(ctx.json()),
                "dff_shared_state": dff_shared_state,
                "used_links": used_links,
                "age_group": age_group,
                "disliked_skills": disliked_skills,
            }

            hype_attr = {"can_continue": can_continue}

            if response_parts:
                hype_attr["response_parts"] = response_parts

            responses.append((text, confidence, human_attr, {}, hype_attr))
        except Exception as exc:
            sentry_sdk.capture_exception(exc)
            logger.exception(exc)
            responses.append(("", 0.0, {}, {}, {}))

    total_time = time.time() - st_time
    logger.info(f"{SERVICE_NAME} exec time = {total_time:.3f}s")
    return responses


try:
    # test_server.run_test(handler)
    logger.info("test query processed")
except Exception as exc:
    sentry_sdk.capture_exception(exc)
    logger.exception(exc)
    raise exc

logger.info(f"{SERVICE_NAME} is loaded and ready")


@app.route("/respond", methods=["POST"])
def respond():
    # import common.test_utils as t_utils; t_utils.save_to_test(request.json,"tests/lets_talk_in.json",indent=4)  # TEST
    # responses = handler(request.json, RANDOM_SEED)  # TEST
    # import common.test_utils as t_utils; t_utils.save_to_test(responses,"tests/lets_talk_out.json",indent=4)  # TEST
    responses = handler(request.json)
    return jsonify(responses)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=SERVICE_PORT)
