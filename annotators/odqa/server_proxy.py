import logging
import os
import requests
import time
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
    odqa_input = request.json
    default_resp = {"qa_system": "odqa",
                    "answer": "",
                    "confidence": 0.0,
                    "answer_pos": 0,
                    "answer_sentence": "",
                    "topical_chat_fact": "",
                    "paragraph": ""}
    odqa_res = [default_resp] * len(odqa_input.get("question_raw", []))
    try:
        st_time = time.time()
        resp = requests.post("http://0.0.0.0:8080/model", json=odqa_input, timeout=1.5)
        if resp.status_code == 200:
            odqa_resp = resp.json()
            if odqa_resp:
                odqa_res = []
                for elem in odqa_resp:
                    if elem and len(elem) == 6:
                        odqa_res.append({"qa_system": "odqa",
                                         "answer": elem[0],
                                         "confidence": float(elem[1]),
                                         "answer_pos": elem[2],
                                         "answer_sentence": elem[3],
                                         "topical_chat_fact": elem[4],
                                         "paragraph": elem[5]})
                    else:
                        odqa_res.append(default_resp)
        logger.info("Respond exec time: " + str(time.time() - st_time))
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)

    return jsonify(odqa_res)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
