import logging
import os
import time
from flask import Flask, request, jsonify
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from deeppavlov import build_model

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
sentry_sdk.init(dsn=os.getenv('SENTRY_DSN'), integrations=[FlaskIntegration()])

intent_responder_intents = set(["exit", "repeat", "where_are_you_from", "who_made_you", "what_is_your_name",
                                "what_is_your_job", "what_can_you_do", "what_time", "dont_understand", "choose_topic",
                                "cant_do", "tell_me_a_story", "get_dialog_id"])

try:
    kgdg = build_model("kg_dial_generator.json", download=False)
    test_res = kgdg(["What is the capital of Russia?"], [["Q159"]])
    logger.info("model loaded, test query processed")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = Flask(__name__)


@app.route("/model", methods=['POST'])
def respond():
    dialogs_batch = request.json["dialogs"]
    sentences = []
    entities = []
    tm_st = time.time()
    for dialog in dialogs_batch:
        uttr = dialog["human_utterances"][-1]
        annotations = uttr["annotations"]
        intents = set(annotations.get('intent_catcher', {}).keys())
        if intents.intersection(intent_responder_intents):
            sentence = ""
        else:
            sentence = uttr.get("text", "")
        sentences.append(sentence)
        if "entity_linking" in annotations:
            entity_ids_batch, _ = annotations["entity_linking"]
            entities.append([entity_ids_list[0] for entity_ids_list in entity_ids_batch])
        else:
            entities.append([])
    if sentences:
        generated_utterances = ["" for _ in sentences]
        confidences = [0.0 for _ in sentences]
    else:
        generated_utterances = [""]
        confidences = [0.0]
    try:
        generated_utterances, confidences = kgdg(sentences, entities)
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
    tm_end = time.time()
    logger.info(f"wikidata dialogue skill exec time {tm_end - tm_st}")

    return jsonify(list(zip(generated_utterances, confidences)))


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
