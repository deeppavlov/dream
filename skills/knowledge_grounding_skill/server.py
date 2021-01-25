import logging
import time
from os import getenv

import requests
import sentry_sdk
from flask import Flask, request, jsonify
from nltk import tokenize

from common.constants import CAN_CONTINUE


sentry_sdk.init(getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

ANNTR_HISTORY_LEN = 3
DEFAULT_CONFIDENCE = 0.85
KNOWLEDGE_GROUNDING_SERVICE_URL = getenv('KNOWLEDGE_GROUNDING_SERVICE_URL')


def get_annotations_from_dialog(utterances, annotator_name, key_name):
    """
    Extract list of strings with values of specific key <key_name>
    from annotator <annotator_name> dict from given dialog utterances.

    Args:
        utterances: utterances, the first one is user's reply
        annotator_name: name of target annotator
        key_name: name of target field from annotation dict

    Returns:
        list of strings with values of specific key from specific annotator
    """
    result_values = []
    for uttr in utterances:
        annotation = uttr.get("annotations", {}).get(annotator_name, {})
        value = annotation.get(key_name, "")
        if value:
            result_values.append(value)
    return result_values


@app.route("/respond", methods=['POST'])
def respond():
    print('response generation started')
    st_time = time.time()
    dialogs_batch = request.json["dialogs"]
    input_batch = []
    attributes = []
    for dialog in dialogs_batch:
        user_input_topic = ""
        user_input_text = dialog["human_utterances"][-1]["text"]

        user_input_history = [i["text"] for i in dialog["utterances"]]
        user_input_history = '\n'.join(user_input_history)

        user_input_knowledge = ""
        # look for kbqa/odqa text in ANNTR_HISTORY_LEN previous human utterances
        annotators = {
            "kbqa": "answer",
            "odqa": "paragraph"
        }
        for anntr_name, anntr_key in annotators.items():
            prev_anntr_outputs = get_annotations_from_dialog(
                dialog["utterances"][-ANNTR_HISTORY_LEN * 2 - 1:],
                anntr_name,
                anntr_key
            )
            logger.debug(f"Prev {anntr_name} {anntr_key}s: {prev_anntr_outputs}")
            if prev_anntr_outputs:
                user_input_knowledge += '\n'.join(tokenize.sent_tokenize(prev_anntr_outputs[-1]))

        user_input = {
            'topic': user_input_topic,
            'knowledge': user_input_knowledge,
            'text': user_input_text,
            'history': user_input_history
        }
        input_batch.append(user_input)
        attributes.append({
            "knowledge_paragraph": user_input_knowledge,
            "knowledge_sentence": tokenize.sent_tokenize(user_input_knowledge)[0] if user_input_knowledge else "",
            "can_continue": CAN_CONTINUE
        })
    try:
        responses = requests.post(KNOWLEDGE_GROUNDING_SERVICE_URL, json={'batch': input_batch}, timeout=1.5)
        if responses.status_code != 200:
            logger.exception(f'service error status code: ' + str(responses.status_code))
        else:
            responses = responses.json()
            logger.info(f"Respond exec time: {time.time() - st_time}")
    except Exception as ex:
        sentry_sdk.capture_exception(ex)
        logger.exception(ex)
    confidences = [DEFAULT_CONFIDENCE] * len(responses)
    return jsonify(list(zip(responses, confidences, attributes)))


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
