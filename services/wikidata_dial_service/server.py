import logging
import os
from flask import Flask, request, jsonify
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from deeppavlov import build_model

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
sentry_sdk.init(dsn=os.getenv('SENTRY_DSN'), integrations=[FlaskIntegration()])

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
    sentences = request.json["sentences"]
    entities = request.json["entities"]
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

    return jsonify([generated_utterances, confidences])


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
