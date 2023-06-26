import logging
import json
from os import getenv
import sentry_sdk
from flask import Flask, request
import requests

# import common.dff.integration.context as int_ctx

sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

gunicorn_logger = logging.getLogger("gunicorn.error")
logger.handlers = gunicorn_logger.handlers
logger.setLevel(gunicorn_logger.level)

app = Flask(__name__)

EXTERNAL_SKILL_URL = getenv("EXTERNAL_SKILL_URL", None)
ARGUMENT_TO_SEND = getenv("ARGUMENT_TO_SEND", "payload")
RESPONSE_KEY = getenv("RESPONSE_KEY", None)

assert "EXTERNAL_SKILL_URL", logger.info(
    "You need to provide the external skill url to get its responses."
)


@app.route("/respond", methods=["POST"])
def respond():
    try:
        dialog = request.json.get("dialogs", [{}])[0]
        dialog_id = dialog.get("dialog_id", "unknown")
        message_text = dialog.get("human_utterances", [{}])[-1].get("text", "")
        result = requests.post(
            EXTERNAL_SKILL_URL,
            json={
                "user_id": f"test-user-000",
                "dialog_id": "dsfmpm545-0j-rbgmoboprgop",
                "payload": "Who are you? who built you? what can you do?",
            },
        )
        logger.info(str(result))
        result = result.json()
        logger.info(str(result))
        payload = {
            "user_id": "test-user-000",
            "dialog_id": dialog_id,
            ARGUMENT_TO_SEND: message_text,
        }
        response = requests.post(EXTERNAL_SKILL_URL, json=payload).json()
        if RESPONSE_KEY:
            response = response[RESPONSE_KEY]
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
        response = ""
    return response


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
