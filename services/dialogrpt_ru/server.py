import logging
import time
import os
from typing import Dict, List

import sentry_sdk
import torch
from flask import Flask, request, jsonify
from healthcheck import HealthCheck
from sentry_sdk.integrations.flask import FlaskIntegration
from transformers import AutoTokenizer, AutoModelForCausalLM


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

PRETRAINED_MODEL_NAME_OR_PATH = os.environ.get(
    "PRETRAINED_MODEL_NAME_OR_PATH", "Grossmend/rudialogpt3_medium_based_on_gpt2"
)
logger.info(f"PRETRAINED_MODEL_NAME_OR_PATH = {PRETRAINED_MODEL_NAME_OR_PATH}")

cuda = torch.cuda.is_available()
if cuda:
    torch.cuda.set_device(0)
    device = "cuda"
else:
    device = "cpu"

logger.info(f"dialogrpt is set to run on {device}")


try:
    model = RussianDialogGPT(PRETRAINED_MODEL_NAME_OR_PATH)
    model.model.eval()
    if cuda:
        model.model.cuda()

    logger.info("dialogpt model is ready")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = Flask(__name__)
health = HealthCheck(app, "/healthcheck")
logging.getLogger("werkzeug").setLevel("WARNING")


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()

    dialog_contexts = request.json.get("dialog_contexts", [])
    num_return_sequences = request.json.get("num_return_sequences", 3)

    try:
        batch_generated_responses = []
        for context in dialog_contexts:
            # context is a list of dicts, each dict contains text and speaker label
            # context = [{"text": "utterance text", "speaker": "human"}, ...]
            inputs = [{"text": uttr["text"], "speaker": 1 if uttr["speaker"] == "bot" else 0} for uttr in context][-3:]
            hypotheses = model.get_responses(inputs, params={"num_return_sequences": num_return_sequences})
            logger.info(f"dialogpt hypotheses: {hypotheses}")
            batch_generated_responses.append(hypotheses)

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        batch_generated_responses = [[]] * len(dialog_contexts)

    total_time = time.time() - st_time
    logger.info(f"dialogpt exec time: {total_time:.3f}s")

    return jsonify({"generated_responses": batch_generated_responses})
