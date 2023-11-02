import logging
import os
import sentry_sdk
import time
import json
from os import getenv

from flask import Flask, request, jsonify
from healthcheck import HealthCheck
from sentry_sdk.integrations.flask import FlaskIntegration

from common.prompts import (
    send_request_to_prompted_generative_service,
    compose_sending_variables,
)


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
health = HealthCheck(app, "/healthcheck")
logging.getLogger("werkzeug").setLevel("WARNING")

GENERATIVE_SERVICE_URL = getenv("GENERATIVE_SERVICE_URL", "http://openai-api-chatgpt:8145/respond")
GENERATIVE_SERVICE_CONFIG = getenv("GENERATIVE_SERVICE_CONFIG", "openai-chatgpt.json")
if GENERATIVE_SERVICE_CONFIG:
    with open(f"common/generative_configs/{GENERATIVE_SERVICE_CONFIG}", "r") as f:
        GENERATIVE_SERVICE_CONFIG = json.load(f)
GENERATIVE_TIMEOUT = float(getenv("GENERATIVE_TIMEOUT", 30.0))
N_UTTERANCES_CONTEXT = int(getenv("N_UTTERANCES_CONTEXT", 1))

ENVVARS_TO_SEND = getenv("ENVVARS_TO_SEND", None)
ENVVARS_TO_SEND = [] if ENVVARS_TO_SEND is None else ENVVARS_TO_SEND.split(",")

available_variables = {f"{var}": getenv(var, None) for var in ENVVARS_TO_SEND}


def make_prompt(sentence, emotion="neutral", mood="happy", intensity=7):
    with open("emotion_change_prompt.txt", "r", encoding="utf-8") as f:
        raw_prompt = f.read()
    sent_prompt = raw_prompt.replace("{SENTENCE}", sentence)
    emot_prompt = sent_prompt.replace("{EMOTION}", emotion)
    mood_prompt = emot_prompt.replace("{MOOD}", mood)
    inten_prompt = mood_prompt.replace("{INTENSITY}", str(intensity))
    return inten_prompt


def get_llm_emotional_response(prompt):
    sending_variables = compose_sending_variables(
        {},
        ENVVARS_TO_SEND,
    )
    try:
        hypotheses = send_request_to_prompted_generative_service(
            [""],
            prompt,
            GENERATIVE_SERVICE_URL,
            GENERATIVE_SERVICE_CONFIG,
            GENERATIVE_TIMEOUT,
            sending_variables,
        )
        response = hypotheses[0]
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
        response = ""

    return response


def rewrite_sentences(sentence, bot_emotion, bot_mood_label):
    result = {}
    try:
        prompt = make_prompt(sentence, bot_emotion, bot_mood_label, 7)  # emotion, mood, intensity
        response = get_llm_emotional_response(prompt)
        result = {"hypotheses": response}
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        result = {"hypotheses": ""}
    return result


@app.route("/respond_batch", methods=["POST"])
def respond_batch():
    st_time = time.time()

    sentences = request.json.get("sentences", [])
    bot_mood_labels = request.json.get("bot_mood_labels", [])
    bot_emotions = request.json.get("bot_emotions", [])

    results = []
    for sentence, emotion, mood in zip(sentences, bot_emotions, bot_mood_labels):
        result = rewrite_sentences(sentence, emotion, mood)
        results.append(result)

    total_time = time.time() - st_time
    logger.info(f"emotional-bot-response exec time: {total_time:.3f}s")

    return jsonify([{"batch": results}])


try:
    logger.info("emotional-bot-response is starting")

    sentences = ["I will eat pizza."]
    bot_mood_labels = ["angry"]
    bot_emotions = ["anger"]
    responses = rewrite_sentences(sentences, bot_mood_labels, bot_emotions)
    logger.info(f"TEST. Sentences: {sentences}")
    logger.info(f"TEST. Emotional sentences: {responses}")

    logger.info("emotional-bot-response is ready")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
