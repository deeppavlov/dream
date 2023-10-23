import logging
import os
import time

from flask import Flask, request, jsonify
import sentry_sdk

from sentry_sdk.integrations.flask import FlaskIntegration
from deeppavlov import build_model

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

logger = logging.getLogger(__name__)

try:
    model = build_model("classifier.json", download=True)
    logger.info("Making test res")
    test_res = model(["a"])
    logger.info("model loaded, test query processed")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = Flask(__name__)

labels = [k.split("\t")[0] for k in open("classes.dict", "r").readlines()]


@app.route("/model", methods=["POST"])
def respond():
    t = time.time()
    sentences = request.json.get("sentences", [" "])
    pred_probs_lists = model(sentences)
    ans = []
    for pred_probs in pred_probs_lists:
        ans.append({dnnc_class: prob for dnnc_class, prob in zip(labels, pred_probs)})
    # roberta config predicted list of class names only - to use it, modify this line
    logger.debug(f"dnnc result: {ans}")
    logger.info(f"dnnc exec time: {time.time() - t}")
    return jsonify(ans)
