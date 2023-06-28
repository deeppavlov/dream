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
ARGUMENT_TO_SEND = getenv("ARGUMENT_TO_SEND")
if not ARGUMENT_TO_SEND:
    ARGUMENT_TO_SEND = "payload"
RESPONSE_KEY = getenv("RESPONSE_KEY")
if not RESPONSE_KEY:
    RESPONSE_KEY = "response"

assert "EXTERNAL_SKILL_URL", logger.info("You need to provide the external skill url to get its responses.")


@app.route("/respond", methods=["POST"])
def respond():
    dialogs = request.json["dialogs"]
    for dialog in dialogs:
        responses = []
        confidences = []
        try:
            dialog_id = dialog.get("dialog_id", None)
            message_text = dialog.get("human_utterances", [{}])[-1].get("text", "")
            payload = {
                "dialog_id": dialog_id,
                ARGUMENT_TO_SEND: message_text,
            }
            result = requests.post(EXTERNAL_SKILL_URL, json=payload).json()
            response = result.get(RESPONSE_KEY, "")
            confidence = result.get("confidence", 0.0)
            logger.info(f"Response: {str(response)}, confidence: {str(confidence)}")
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
