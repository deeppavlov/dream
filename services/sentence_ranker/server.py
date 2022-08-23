import logging
import os
import time
from typing import List, Tuple

import sentry_sdk
import torch
from flask import Flask, request, jsonify
from sentry_sdk.integrations.flask import FlaskIntegration
from torch.nn import functional as F
from transformers import AutoModel, AutoTokenizer


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

PRETRAINED_MODEL_NAME_OR_PATH = os.environ.get("PRETRAINED_MODEL_NAME_OR_PATH", "dialogrpt_ru_ckpt_v0.pth")
logger.info(f"PRETRAINED_MODEL_NAME_OR_PATH = {PRETRAINED_MODEL_NAME_OR_PATH}")

try:
    tokenizer = AutoTokenizer.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH)
    model = AutoModel.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH)
    if torch.cuda.is_available():
        model.to("cuda")
        logger.info("sentence-ranker is set to run on cuda")

    logger.info("sentence-ranker is ready")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel("WARNING")


def get_pair_embeddings(sentence_pairs_batch: List[Tuple[str]]):
    inputs = tokenizer.batch_encode_plus(sentence_pairs_batch, return_tensors="pt", padding=True)
    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"]
    if torch.cuda.is_available():
        input_ids = input_ids.cuda()
        attention_mask = attention_mask.cuda()
    outputs = model(input_ids, attention_mask=attention_mask)
    embeddings = []
    for output in outputs:
        embeddings += [(output[:1].mean(dim=1), output[1:].mean(dim=1))]
    return embeddings


def get_sim_for_pair_embeddings(sentence_pairs_batch: List[Tuple[str]]):
    embeddings = get_pair_embeddings(sentence_pairs_batch)
    scores = []
    for emb_pair in embeddings:
        result = F.cosine_similarity(emb_pair[0], emb_pair[1])
        scores += [result]
    return scores


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    sentence_pairs = request.json.get("sentence_pairs", [])

    try:
        scores = get_sim_for_pair_embeddings(sentence_pairs)
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        scores = [0.] * len(sentence_pairs)

    total_time = time.time() - st_time
    logger.info(f"sentence-ranker exec time: {total_time:.3f}s")
    return scores
