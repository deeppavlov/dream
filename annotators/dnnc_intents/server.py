import os
import time

from flask import Flask, request, jsonify
import sentry_sdk

from sentry_sdk.integrations.flask import FlaskIntegration
from deeppavlov import build_model
from common.combined_classes import combined_classes
from common.dnnc_classes import dnnc_classes

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


@app.route("/model", methods=["POST"])
def respond():
    t = time.time()
    sentences = request.json.get("sentences", [" "])
    label_list = model(sentences)
    ans=[]
    for sentence in sentences:
        ans.append({dnnc_class:1 for dnnc_class in label_list}
    return jsonify(ans)
