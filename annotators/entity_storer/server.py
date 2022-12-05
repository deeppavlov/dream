import logging
import time
import os

from flask import Flask, request, jsonify
from healthcheck import HealthCheck
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

import common.entity_utils as entity_utils
import test_server

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
health = HealthCheck(app, "/healthcheck")
logging.getLogger("werkzeug").setLevel("WARNING")


def in_last_utts(last_utts, entity):
    for utt in last_utts:
        if entity in utt:
            logger.info(f"Entity {entity} occurred in prev Bot Utterances: {utt}")
            return True
    return False


def handler(requested_data):
    st_time = time.time()

    dialogs = requested_data.get("dialogs", [])

    human_utter_indexes = requested_data.get("human_utter_indexes", [0] * len(dialogs))
    responses = []
    for dialog, human_utter_index in zip(dialogs, human_utter_indexes):
        try:
            human_attr = dialog.get("human", {}).get("attributes", {})
            bot_utts = dialog.get("bot_utterances", [])
            last_bot_utts = []
            for i in range(min(len(bot_utts), 5)):
                last_bot_utts.append(bot_utts[i].get("text", ""))

            entities = human_attr.get("entities", {})
            entities = entity_utils.load_raw_entities(entities)
            entities = entity_utils.update_entities(dialog, human_utter_index, entities)
            human_attr = {"entities": {k: dict(v) for k, v in entities.items()}}
            keys = list(human_attr["entities"].keys())
            for ent in keys:
                if in_last_utts(last_bot_utts, ent):
                    human_attr["entities"][ent]["mentioned"] = True
                else:
                    human_attr["entities"][ent]["mentioned"] = False
            logger.info(f"Human attributes: {human_attr}")
        except Exception as exc:
            logger.exception(exc)
            sentry_sdk.capture_exception(exc)
            human_attr = {}
        responses += [{"human_attributes": human_attr}]
    total_time = time.time() - st_time
    logger.info(f"entity_storer exec time: {total_time:.3f}s")
    return responses


try:
    test_server.run_test(handler)
    logger.info("test query processed")
except Exception as exc:
    sentry_sdk.capture_exception(exc)
    logger.exception(exc)
    raise exc


@app.route("/respond", methods=["POST"])
def respond():
    # next commented line for test creating
    # import pathlib;import json;json.dump(request.json,pathlib.Path("tests/create_update_in.json").open("wt"),indent=4)
    responses = handler(request.json)
    # next commented line for test creating
    # import pathlib;import json;json.dump(responses, pathlib.Path("tests/create_update_out.json").open("wt"), indent=4)
    return jsonify(responses)
