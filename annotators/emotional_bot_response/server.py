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

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
health = HealthCheck(app, "/healthcheck")
logging.getLogger("werkzeug").setLevel("WARNING")

GENERATIVE_SERVICE_URL = getenv(
    "GENERATIVE_SERVICE_URL", "http://openai-api-chatgpt:8145/respond"
)
GENERATIVE_SERVICE_CONFIG = getenv("GENERATIVE_SERVICE_CONFIG", "openai-chatgpt.json")
if GENERATIVE_SERVICE_CONFIG:
    with open(f"common/generative_configs/{GENERATIVE_SERVICE_CONFIG}", "r") as f:
        GENERATIVE_SERVICE_CONFIG = json.load(f)
GENERATIVE_TIMEOUT = int(getenv("GENERATIVE_TIMEOUT", 30))
N_UTTERANCES_CONTEXT = int(getenv("N_UTTERANCES_CONTEXT", 1))

ENVVARS_TO_SEND = getenv("ENVVARS_TO_SEND", None)
ENVVARS_TO_SEND = [] if ENVVARS_TO_SEND is None else ENVVARS_TO_SEND.split(",")

available_variables = {f"{var}": getenv(var, None) for var in ENVVARS_TO_SEND}

API_CONFIGS = getenv("API_CONFIGS", None)
API_CONFIGS = [] if API_CONFIGS is None else API_CONFIGS.split(",")
api_conf = {}
for config in API_CONFIGS:
    with open(f"api_configs/{config}", "r") as f:
        conf = json.load(f)
        api_conf.update(conf)

for key, value in api_conf.copy().items():
    for api_key in value["keys"]:
        if not available_variables[api_key]:
            del api_conf[key]
            break

logger.info(
    f"Available APIs: {', '.join([api['display_name'] for api in api_conf.values()])}"
)


def timeout_handler():
    raise Exception("API timeout")


def make_prompt(sentence, emotion="neutral", mood="happy", intensity=7):
    prompt = f"""You are a writer who needs to rewrite a sentence to express
    specific emotions, moods, and intensity levels. Your task is to generate
    a new sentence that conveys the desired emotions, moods, and emotion intensity
    (0 represents minimal intensity and 10 represents maximum intensity)
    while keeping the original meaning and vocabulary range.
    Here's the information you have:

    **Input:**
    - Sentence: {sentence}
    - Emotion Label: {emotion}
    - Mood Label: {mood}
    - Intensity Level: {intensity}

    **Instructions:**
    1. Read the given sentence and understand its meaning and context.
    2. Rewrite the sentence to include the specified emotion, mood, and intensity.
    Make changes to the wording, sentence structure, and choice of words as needed.
    Ensure that the new sentence effectively conveys the desired emotions, moods,
    and intensity but preserves vocabulary range of the original.
    3. Pay attention to the overall tone, mood, and intensity of the sentence.
    Adjust the sentence's tone and word choice to match the specified mood label
    and intensity level, while considering the emotional undertones associated
    with the selected emotion label.
    4. Maintain the original meaning of the sentence. Although you can rephrase
    and restructure the sentence, ensure that the core idea remains the same.

    **Example:**

    **Input:**
    - Sentence: I quit my job.
    - Emotion Label: anger
    - Mood Label: frustrated
    - Intensity Level: 5

    **Instructions:**
    1. Read the given sentence and understand its meaning and context:
    The person decided to leave their job.
    2. Rewrite the sentence to include the specified emotion, mood, and intensity.
    3. Adjust the sentence's tone, word choice, and intensity level: Use stronger
    and more impactful words that convey a high level of anger and frustration,
    reflecting the intensity level specified.
    4. Maintain the original meaning of the sentence: Ensure that the person still
    expresses the decision to leave their job.

    **Example Output:**
    I've had it! I'm done with this pathetic excuse for a job!

    Remember, your task is to rewrite sentences according to specified emotions,
    moods, and intensity levels while keeping the original meaning and vocabulary range.
    Feel free to adjust sentence structures and choose words that effectively convey
    the desired emotions, moods, and intensity. Keep the language complexity simple.
    Don't mention intensity level in the output. Preserve the type of the sentence
    if it is a question.

    **Output:**"""
    return prompt


def get_llm_emotional_response(prompt):
    sending_variables = compose_sending_variables(
        {},
        ENVVARS_TO_SEND,
    )
    try:
        hypotheses = send_request_to_prompted_generative_service(
            "",
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
        response = None

    return response


def rewrite_sentences(sentence, bot_emotion, bot_mood_label):
    result = {}
    try:
        prompt = make_prompt(
            sentence, bot_emotion, bot_mood_label, 7
        )  # emotion, mood, intensity
        response = get_llm_emotional_response(prompt)
        result = {"hypotheses": response}
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        result = {"hypotheses": "fallback standard response"}
    return result


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()

    sentences = request.json.get("sentences", [])
    bot_mood_label = request.json.get("bot_mood_label", [])
    bot_emotion = request.json.get("bot_emotion", [])

    results = []
    for i in range(len(sentences)):
        result = rewrite_sentences(sentences[i], bot_emotion[0], bot_mood_label[0])
        results.append(result)

    total_time = time.time() - st_time
    logger.info(f"emotional-bot-response exec time: {total_time:.3f}s")

    return jsonify(results)


@app.route("/respond_batch", methods=["POST"])
def respond_batch():
    st_time = time.time()

    sentences = request.json.get("sentences", [])
    bot_mood_label = request.json.get("bot_mood_label", [])
    bot_emotion = request.json.get("bot_emotion", [])

    results = []
    for i in range(len(sentences)):
        result = rewrite_sentences(sentences[i], bot_emotion[i], bot_mood_label[i])
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
    logger.info("TEST. Sentences: {}".format(sentences))
    logger.info("TEST. Emotional sentences: {}".format(responses))

    logger.info("emotional-bot-response is ready")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
