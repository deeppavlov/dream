import logging
import os
import requests
import time
from flask import Flask, request, jsonify
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

intent_responder_intents = set(
    [
        "exit",
        "repeat",
        "where_are_you_from",
        "who_made_you",
        "what_is_your_name",
        "what_is_your_job",
        "what_can_you_do",
        "what_time",
        "dont_understand",
        "choose_topic",
        "cant_do",
        "tell_me_a_story",
        "get_dialog_id",
    ]
)

app = Flask(__name__)

WIKIDATA_DIALOGUE_SERVICE_URL = os.getenv("WIKIDATA_DIALOGUE_SERVICE_URL")
LOWER_LIMIT = 0.6


@app.route("/model", methods=["POST"])
def respond():
    dialogs_batch = request.json["dialogs"]
    sentences = []
    entities = []
    tm_st = time.time()
    for dialog in dialogs_batch:
        uttr = dialog["human_utterances"][-1]
        annotations = uttr["annotations"]
        intents = set(annotations.get("intent_catcher", {}).keys())
        if intents.intersection(intent_responder_intents):
            sentence = ""
        else:
            sentence = uttr.get("text", "")
        sentences.append(sentence)
        entities_inp = []
        try:
            if "entity_linking" in annotations:
                entity_info_list = annotations["entity_linking"]
                if entity_info_list:
                    if isinstance(entity_info_list[0], dict):
                        for entity_info in entity_info_list:
                            if "entity_ids" in entity_info and entity_info["entity_ids"]:
                                entities_inp.append(entity_info["entity_ids"][0])
                    if isinstance(entity_info_list[0], list):
                        entity_ids_batch, conf = entity_info_list
                        for entity_ids_list in entity_ids_batch:
                            if entity_ids_list:
                                entities_inp.append(entity_ids_list[0])
        except Exception as e:
            sentry_sdk.capture_exception(e)
            logger.exception(e)
        entities.append(entities_inp)
    if sentences:
        generated_utterances = ["" for _ in sentences]
        confidences = [0.0 for _ in sentences]
    else:
        generated_utterances = [""]
        confidences = [0.0]
    try:
        res = requests.post(
            WIKIDATA_DIALOGUE_SERVICE_URL, json={"sentences": sentences, "entities": entities}, timeout=1.5
        )
        if res.status_code == 200:
            generated_utterances, confidences = res.json()
            for i in range(len(confidences)):
                if confidences[i] < LOWER_LIMIT:
                    confidences[i] = LOWER_LIMIT
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
    tm_end = time.time()
    logger.info(f"wikidata dialogue skill exec time {tm_end - tm_st}")

    return jsonify(list(zip(generated_utterances, confidences)))


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
