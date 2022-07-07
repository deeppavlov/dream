import logging
import time
import os
import pickle
from pathlib import Path

import sentry_sdk
import tokenize_util
import torch
from flask import Flask, request, jsonify
from infer import infill_with_ilm
from sentry_sdk.integrations.flask import FlaskIntegration
from transformers import GPT2LMHeadModel


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_DIR = os.environ.get("MODEL_DIR", "/data/")
logging.info(f"MODEL_DIR = {MODEL_DIR}")
# MASK_ID = 103

try:
    if torch.cuda.is_available():
        device = torch.device("cuda")
    else:
        device = torch.device("cpu")

    logger.info(f"infilling is set to run on {device}")

    # init model
    tokenizer = tokenize_util.Tokenizer.GPT2
    with open(Path(MODEL_DIR).joinpath("additional_ids_to_tokens.pkl"), "rb") as f:
        additional_ids_to_tokens = pickle.load(f)
    additional_tokens_to_ids = {v: k for k, v in additional_ids_to_tokens.items()}
    try:
        tokenize_util.update_tokenizer(additional_ids_to_tokens, tokenizer)
    except ValueError:
        logger.info("Tokenizer already updated")
    logger.info(additional_tokens_to_ids)
    model = GPT2LMHeadModel.from_pretrained(MODEL_DIR)
    model.eval()
    if torch.cuda.is_available():
        additional_tokens_to_ids = {
            k: torch.tensor(v, dtype=torch.int).cuda() for k, v in additional_tokens_to_ids.items()
        }
        model.to(device)

    logger.info("infilling model is ready")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = Flask(__name__)


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()

    texts = request.json.get("texts", [])
    logger.info(f"Input: {texts}")
    try:
        output = []
        for txt in texts:
            inputs = tokenize_util.encode(txt, tokenizer)
            _blank_id = tokenize_util.encode(" _", tokenizer)[0]
            flag = 0
            while not flag:  # надо исправить костыль
                try:
                    inputs[inputs.index(_blank_id)] = additional_tokens_to_ids["<|infill_ngram|>"]
                except Exception:
                    flag = 1
            generated = infill_with_ilm(model, additional_tokens_to_ids, inputs, num_infills=1)
            output.append(tokenize_util.decode(generated[0], tokenizer))
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        output = [""] * len(texts)

    logger.info(f"Output: {output}")
    total_time = time.time() - st_time
    logger.info(f"infilling exec time: {total_time:.3f}s")
    return jsonify({"infilled_text": output})
