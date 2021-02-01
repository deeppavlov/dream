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

config_name = os.getenv("CONFIG")

try:
    odqa = build_model(config_name, download=True)
    test_res = odqa(["What is the capital of Russia?"])
    logger.info("model loaded, test query processed")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = Flask(__name__)


@app.route("/model", methods=['POST'])
def respond():
    questions = request.json.get("question_raw", [" "])
    questions = [question.lstrip("alexa") for question in questions]
    res = []
    try:
        res = odqa(questions)
        res = [[elem[i] for elem in res] for i in range(len(res[0]))]
        for i in range(len(res)):
            res[i][1] = float(res[i][1])
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
    return jsonify(res)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
