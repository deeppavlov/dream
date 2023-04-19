import logging
import time
from os import getenv

from transformers import AutoTokenizer, T5ForConditionalGeneration
import torch
import sentry_sdk
from flask import Flask, jsonify, request


sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
device = 'cuda' if torch.cuda.is_available() else 'cpu'

app = Flask(__name__)

model = T5ForConditionalGeneration.from_pretrained('IlyaGusev/rut5_base_sum_gazeta')
model.to(device)
tokenizer = AutoTokenizer.from_pretrained('IlyaGusev/rut5_base_sum_gazeta')
logger.info("Model is loaded.")


@app.route("/respond_batch", methods=["POST"])
def respond_batch():
    start_time = time.time()
    sentences = request.json.get("sentences", [])
    logger.debug(f"Sentences: {sentences}")
    tokenized_text = tokenizer(sentences, max_length=512, add_special_tokens=True, return_tensors="pt",
                               truncation=True, padding='max_length').to(device)
    summary = model.generate(tokenized_text['input_ids'])
    summary = tokenizer.batch_decode(summary, skip_special_tokens=True)
    total_time = time.time() - start_time
    logger.info(f"rut5-summarizer exec time: {round(total_time, 2)} sec")
    return jsonify([{"batch": summary}])


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8154)
