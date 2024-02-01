"""
model has been trained on 7 different languages so it should only be tested on:
english, french, spanish, italian, portuguese, turkish or russian.
"""

import logging
import time
import os

import sentry_sdk
import torch
from flask import Flask, request, jsonify
from sentry_sdk.integrations.flask import FlaskIntegration
import transformers

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

PRETRAINED_MODEL_NAME_OR_PATH = os.environ.get("PRETRAINED_MODEL_NAME_OR_PATH")
logging.info(f"PRETRAINED_MODEL_NAME_OR_PATH = {PRETRAINED_MODEL_NAME_OR_PATH}")


try:
    loaded = torch.hub.load_state_dict_from_url(PRETRAINED_MODEL_NAME_OR_PATH)
    class_names = loaded["config"]["dataset"]["args"]["classes"]
    model_type = loaded["config"]["arch"]["args"]["model_type"]
    model_name = loaded["config"]["arch"]["args"]["model_name"]
    tokenizer_name = loaded["config"]["arch"]["args"]["tokenizer_name"]
    num_classes = loaded["config"]["arch"]["args"]["num_classes"]

    model_class = getattr(transformers, model_name)
    model = model_class.from_pretrained(
        pretrained_model_name_or_path=None,
        config=model_type,
        num_labels=num_classes,
        state_dict=loaded["state_dict"],
        local_files_only=False,
    )
    model.eval()
    if torch.cuda.is_available():
        model.to("cuda")
        logger.info("toxic-classification is set to run on cuda")
    tokenizer = getattr(transformers, tokenizer_name).from_pretrained(
        model_type,
        local_files_only=False,
    )
    logger.info("toxic-classification is ready")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel("WARNING")


def classify_sentences(sentences):
    try:
        inputs = tokenizer(sentences, return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            if torch.cuda.is_available():
                inputs = inputs.to("cuda")
            outputs = model(**inputs)[0]
            model_output = torch.sigmoid(outputs).detach().cpu().numpy()
            result = []

            for i, cla in zip(sentences, model_output):
                result += [{class_names[id_column]: float(cla[id_column]) for id_column in range(len(class_names))}]

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        result = [{column: 0.0 for column in class_names}] * len(sentences)
    logger.info(result)
    return result


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    sentences = request.json.get("sentences", [])
    result = classify_sentences(sentences)
    total_time = time.time() - st_time
    logger.info(f"toxic-classification exec time: {total_time:.3f}s")

    return jsonify(result)


@app.route("/respond_batch", methods=["POST"])
def respond_batch():
    st_time = time.time()
    sentences = request.json.get("sentences", [])
    result = classify_sentences(sentences)
    total_time = time.time() - st_time
    logger.info(f"toxic-classification exec time: {total_time:.3f}s")

    return jsonify([{"batch": result}])
