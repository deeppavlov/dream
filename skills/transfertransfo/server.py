import logging
import os
import random
import time
from os import getenv

import sentry_sdk
import torch
from flask import Flask, request, jsonify
from flasgger import Swagger, swag_from
from pytorch_pretrained_bert import OpenAIGPTLMHeadModel, OpenAIGPTTokenizer

from interact import sample_sequence

sentry_sdk.init(getenv("SENTRY_DSN"))

SEED = 31415
DEVICE = os.getenv("DEVICE", "cpu")  # cuda or cpu
MAX_HISTORY = 2
MAX_LENGTH = 20
MIN_LENGTH = 1
MODEL = "gpt"
MODEL_PATH = os.getenv("MODEL_PATH", "./models")
TEMPERATURE = 0.7
TOP_K = 0
TOP_P = 0.9
NO_SAMPLE = True


def args():
    None


args.max_length = MAX_LENGTH
args.device = DEVICE
args.model = MODEL
args.temperature = TEMPERATURE
args.top_k = TOP_K
args.top_p = TOP_P
args.no_sample = NO_SAMPLE
args.min_length = MIN_LENGTH

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(module)s %(lineno)d %(levelname)s : %(message)s",
    handlers=[
        logging.StreamHandler(),
        # logging.FileHandler("../logs/{}.log".format(date)),
    ],
)

logger = logging.getLogger(__name__)

app = Flask(__name__)
swagger = Swagger(app)


random.seed(SEED)
torch.random.manual_seed(SEED)
torch.cuda.manual_seed(SEED)

tokenizer_class = OpenAIGPTTokenizer
tokenizer = tokenizer_class.from_pretrained(MODEL_PATH)
model_class = OpenAIGPTLMHeadModel
model = model_class.from_pretrained(MODEL_PATH)

model.to(DEVICE)
model.eval()


def inference(personality, utterances_histories):
    personality = [tokenizer.encode(ut) for ut in personality]
    history = [tokenizer.encode(ut) for ut in utterances_histories]
    history = history[-(2 * MAX_HISTORY + 1) :]
    with torch.no_grad():
        out_ids, out_probs = sample_sequence(personality, history, tokenizer, model, args)
    if out_probs:
        return tokenizer.decode(out_ids, skip_special_tokens=True), float(sum(out_probs) / len(out_probs))
    else:
        return "", 0.0


@app.route("/transfertransfo", methods=['POST'])
@swag_from('chitchat_endpoint.yml')
def transfer_transfo_chitchat_model():
    st_time = time.time()
    personality = request.json['personality']
    utterances_histories = request.json['utterances_histories']
    response = [
        inference(pers, hist) for pers, hist in zip(personality, utterances_histories)
    ]
    total_time = time.time() - st_time
    logger.info(f"transfertransfo exec time: {total_time:.3f}s")
    return jsonify(response)
