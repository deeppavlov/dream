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
    kbqa_res = [("Not Found", 0.0)] * len(questions.get("x_init", []))
    try:
        resp = requests.post("http://0.0.0.0:8080/model", json=questions, timeout=1.5)
        if resp.status_code == 200:
            kbqa_res = resp.json()
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)

    return jsonify({"kbqa_res": kbqa_res})


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
