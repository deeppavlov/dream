import logging
import time
import os

import sentry_sdk
import torch
from flask import Flask, request, jsonify
from sentry_sdk.integrations.flask import FlaskIntegration
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoModel, AutoTokenizer


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

PRETRAINED_MODEL_NAME_OR_PATH = os.environ.get(
    "PRETRAINED_MODEL_NAME_OR_PATH", "DeepPavlov/bert-base-multilingual-cased-sentence"
)
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


def get_sim_for_pair_embeddings(sentence_pairs_batch):
    # source code: https://towardsdatascience.com/bert-for-measuring-text-similarity-eec91c6bf9e1
    # initialize dictionary to store tokenized sentences
    tokens = {"input_ids": [], "attention_mask": []}

    for pair in sentence_pairs_batch:
        # encode each sentence and append to dictionary
        for sentence in pair:
            new_tokens = tokenizer.encode_plus(
                sentence, max_length=64, truncation=True, padding="max_length", return_tensors="pt"
            )
            tokens["input_ids"].append(new_tokens["input_ids"][0])
            tokens["attention_mask"].append(new_tokens["attention_mask"][0])

    # reformat list of tensors into single tensor
    tokens["input_ids"] = torch.stack(tokens["input_ids"])
    tokens["attention_mask"] = torch.stack(tokens["attention_mask"])
    if torch.cuda.is_available():
        tokens["input_ids"] = tokens["input_ids"].cuda()
        tokens["attention_mask"] = tokens["attention_mask"].cuda()

    embeddings = model(**tokens).last_hidden_state
    attention_mask = tokens["attention_mask"]
    mask = attention_mask.unsqueeze(-1).expand(embeddings.size()).float()
    masked_embeddings = embeddings * mask
    summed = torch.sum(masked_embeddings, 1)
    summed_mask = torch.clamp(mask.sum(1), min=1e-9)
    mean_pooled = summed / summed_mask
    # convert from PyTorch tensor to numpy array
    if torch.cuda.is_available():
        mean_pooled = mean_pooled.cpu()
    mean_pooled = mean_pooled.detach().numpy()

    # calculate
    scores = []
    for i in range(len(sentence_pairs_batch)):
        scores += [cosine_similarity([mean_pooled[i * 2]], [mean_pooled[i * 2 + 1]]).tolist()[0][0]]
    return scores


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    sentence_pairs = request.json.get("sentence_pairs", [])

    try:
        scores = get_sim_for_pair_embeddings(sentence_pairs)
        logger.info(f"sentence-ranker output: {scores}")
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        scores = [0.0] * len(sentence_pairs)

    total_time = time.time() - st_time
    logger.info(f"sentence-ranker exec time: {total_time:.3f}s")
    return jsonify([{"batch": scores}])
