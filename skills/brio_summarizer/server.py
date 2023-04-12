import logging
import time
from os import getenv

from transformers import BartTokenizer, BartForConditionalGeneration
import sentry_sdk
from flask import Flask, jsonify, request


sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)

model = BartForConditionalGeneration.from_pretrained('Yale-LILY/brio-cnndm-uncased')
tokenizer = BartTokenizer.from_pretrained('Yale-LILY/brio-cnndm-uncased')
logger.info("Model is loaded.")


@app.route("/respond", methods=["POST"])
def respond_batch():
    start_time = time.time()
    sentences = request.json.get("sentences", [])
    logger.debug(f"Sentences: {sentences}")
    tokenized_text = tokenizer(sentences, max_length=512, return_tensors="pt", truncation=True)
    summary = model.generate(tokenized_text['input_ids'])
    summary = tokenizer.batch_decode(summary, skip_special_tokens=True)
    total_time = time.time() - start_time
    logger.info(f"brio-summarizer exec time: {round(total_time, 2)} sec")
    return jsonify([{"batch": summary}])


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8153)
