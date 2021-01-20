import logging
import os
import requests
from flask import Flask, request, jsonify
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
sentry_sdk.init(dsn=os.getenv('SENTRY_DSN'), integrations=[FlaskIntegration()])

app = Flask(__name__)


@app.route("/model", methods=['POST'])
def respond():
    questions = request.json
    odqa_res = [["", 0.0, 0, "", ""]] * len(questions.get("question_raw", []))
    try:
        resp = requests.post("http://0.0.0.0:8080/model", json=questions, timeout=1.5)
        if resp.status_code == 200:
            odqa_resp = resp.json()
            if odqa_resp and odqa_resp[0]:
                odqa_res = [[elem[i] for elem in odqa_resp] for i in range(len(odqa_resp[0]))]
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)

    return jsonify({"odqa_res": odqa_res})


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
