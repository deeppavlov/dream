import logging
import os
import time
from flask import Flask, request, jsonify
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from deeppavlov import build_model

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

config_name = os.getenv("CONFIG")

try:
    qa = build_model(config_name, download=True)
    test_res = qa(["What is the capital of Russia?"], [["Moscow is the capital of Russia."]])
    logger.info("model loaded, test query processed")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = Flask(__name__)


@app.route("/model", methods=["POST"])
def respond():
    questions = request.json.get("question_raw", [" "])
    facts = request.json.get("top_facts", [[" "]])

    qa_res = [["", 0.0, 0, ""] for _ in questions]
    try:
        tm_st = time.time()
        logger.info(f"questions {questions} facts {facts}")
        qa_res = qa(questions, facts)
        qa_res = [[elem[i] for elem in qa_res] for i in range(len(qa_res[0]))]
        for i in range(len(qa_res)):
            qa_res[i][1] = float(qa_res[i][1])
        logger.info(f"text_qa exec time: {time.time() - tm_st} qa_res {qa_res}")
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
    return jsonify(qa_res)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
