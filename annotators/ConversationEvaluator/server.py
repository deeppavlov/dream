import logging
import os
import time

from flask import Flask, request, jsonify
import sentry_sdk

from sentry_sdk.integrations.flask import FlaskIntegration
from deeppavlov import build_model

logger = logging.getLogger(__name__)
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])


def transform(data):
    dialogs = []
    utterances = []
    for past_uttr, past_response in zip(data["pastUtterances"], data["pastResponses"]):
        utterances.append(past_uttr)
        utterances.append(past_response)
    utterances.append(data["currentUtterance"])
    for hyp in data["hypotheses"]:
        dialogs.append(" [SEP]".join(utterances + [hyp]))
    return dialogs


try:
    model = build_model("conveval.json", download=False)
    test_res = model(["a"])
    logger.info("model loaded, test query processed")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = Flask(__name__)


@app.route("/batch_model", methods=["POST"])
def batch_respond():
    t = time.time()
    data = transform(request.json)
    conv_eval_results = model(data)
    key_annotations = [
        "isResponseComprehensible",
        "isResponseErroneous",
        "isResponseInteresting",
        "isResponseOnTopic",
        "responseEngagesUser",
    ]
    result = []
    for scores in conv_eval_results:
        result.append({annotation: float(score) for annotation, score in zip(key_annotations, scores)})
    logger.info(f"Conv eval exec time {round(time.time()-t, 2)} sec")
    return jsonify([{"batch": result}])


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
