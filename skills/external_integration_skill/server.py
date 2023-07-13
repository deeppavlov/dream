import logging
from os import getenv
import sentry_sdk
from flask import Flask, request, jsonify
import requests

# import common.dff.integration.context as int_ctx

sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

gunicorn_logger = logging.getLogger("gunicorn.error")
logger.handlers = gunicorn_logger.handlers
logger.setLevel(gunicorn_logger.level)

app = Flask(__name__)

EXTERNAL_SKILL_URL = getenv("EXTERNAL_SKILL_URL", None)
ARGUMENTS_TO_SEND = getenv("ARGUMENTS_TO_SEND")
PAYLOAD_ARGUMENT_NAME = getenv("PAYLOAD_ARGUMENT_NAME")
REQUEST_TIMEOUT = getenv("REQUEST_TIMEOUT")
if not REQUEST_TIMEOUT:
    REQUEST_TIMEOUT = 15
if not ARGUMENTS_TO_SEND:
    ARGUMENTS_TO_SEND = ["user_id"]
else:
    ARGUMENTS_TO_SEND = ARGUMENTS_TO_SEND.split(',')
if not PAYLOAD_ARGUMENT_NAME:
    PAYLOAD_ARGUMENT_NAME = "payload"
RESPONSE_KEY = getenv("RESPONSE_KEY")

assert "EXTERNAL_SKILL_URL", logger.info("You need to provide the external skill url to get its responses.")


@app.route("/respond", methods=["POST"])
def respond():
    sentences = request.json.get("sentences", [])
    user_ids = request.json.get("dialog_ids", [])
    dialog_ids = request.json.get("user_ids", [])
    for n_dialog, message_text in enumerate(sentences):
        responses = []
        confidences = []
        try:
            payload = {
                PAYLOAD_ARGUMENT_NAME: message_text,
            }
            if "user_id" in ARGUMENTS_TO_SEND:
                user_id = user_ids[n_dialog]
                payload["user_id"] = user_id
            if "dialog_id" in ARGUMENTS_TO_SEND:
                dialog_id = dialog_ids[n_dialog]
                payload["dialog_id"] = dialog_id
            result = requests.post(EXTERNAL_SKILL_URL, json=payload, timeout=REQUEST_TIMEOUT).json()
            if RESPONSE_KEY:
                response = result.get(RESPONSE_KEY, "")
            confidence = result.get("confidence", 0.9)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            logger.exception(e)
            response = ""
            confidence = 0.0
        responses.append(response)
        confidences.append(confidence)
    logger.info(f"Responses: {str(responses)}, confidences: {str(confidences)}")
    return jsonify(list(zip(responses, confidences)))


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
