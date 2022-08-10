import logging
import time
import os

import sentry_sdk
import torch
from flask import Flask, request, jsonify
from sentry_sdk.integrations.flask import FlaskIntegration
from transformers import GPT2Tokenizer, GPT2LMHeadModel
from transformers import BartForConditionalGeneration, BartTokenizer
from string import punctuation

import nltk
from nltk.corpus import stopwords
import re
from nltk.tokenize import sent_tokenize

nltk.download("stopwords")
nltk.download("punkt")
stop_words = stopwords.words("english")

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_CONFIDENCE = 0.9
ZERO_CONFIDENCE = 0.0
pattern = re.compile(r"\(.*?\)")

try:
    tokenizer = GPT2Tokenizer.from_pretrained("/data/finetuned2")
    tokenizer.padding_side = "left"
    tokenizer.pad_token = tokenizer.eos_token
    model = GPT2LMHeadModel.from_pretrained("/data/finetuned2")
    bart_model = BartForConditionalGeneration.from_pretrained("facebook/bart-large", forced_bos_token_id=0)
    bart_tok = BartTokenizer.from_pretrained("facebook/bart-large")
    if torch.cuda.is_available():
        device = "cuda"
    else:
        device = "cpu"
    model.to(device)
    logger.info(f"prompt_storygpt is set to run on {device}")
    logger.info("prompt_storygpt is ready")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel("WARNING")


def generate_part(texts, max_len, temp, num_sents, first):
    if not first:
        texts = [text + " At the end," for text in texts]
    encoding = tokenizer(texts, padding=True, return_tensors="pt").to(device)
    with torch.no_grad():
        generated_ids = model.generate(
            **encoding, max_length=max_len, length_penalty=-100.0, temperature=temp, do_sample=True
        )
    generated_texts = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)

    return_texts = []
    for text in generated_texts:
        text = pattern.sub("", text)  # delete everything in ()
        text = text.replace(" .", ".").replace("..", ".").replace("..", ".")
        sents = sent_tokenize(text)
        text = " ".join(sents[:num_sents])
        if text[-1] not in ".!?":
            if text[-1] in punctuation:
                text = text[:-1]
            text += "."
        return_texts.append(text)
    return return_texts


def fill_mask(masked_phrases):
    batch = bart_tok(masked_phrases, return_tensors="pt")
    generated_ids = bart_model.generate(batch["input_ids"])
    filled = bart_tok.batch_decode(generated_ids, skip_special_tokens=True)
    logger.info(f"Filled masks: {filled}")
    return filled


def generate_response(context):
    """
    Parameters
    context: List[str]
        a list consisting of nouns chosen from spacy_nounphrases annotator
    Returns
    final_text: List[str]
        generated stories
    """
    nouns = context
    logger.info(f"Topic in StoryGPT service: {nouns}")
    masked_phrases = []
    for noun in nouns:
        masked_phrases.append(f"Let me share a story about {noun[0]}. I <mask> {noun[0]}")
    filled = fill_mask(masked_phrases)
    first_texts = generate_part(filled, 100, 1, 4, first=True)
    logger.info(f"First parts generated: {first_texts}")
    final_texts = generate_part(first_texts, 150, 0.8, 5, first=False)
    logger.info(f"Generated: {final_texts}")
    return final_texts


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    contexts = request.json.get("utterances_histories", [])

    try:
        tmp_responses = generate_response(contexts)
        responses = []
        confidences = []
        for response in tmp_responses:
            if len(response) > 3:
                # drop too short responses
                responses += [response]
                confidences += [DEFAULT_CONFIDENCE]
            else:
                responses += [""]
                confidences += [ZERO_CONFIDENCE]
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        responses = [""] * len(contexts)
        confidences = [ZERO_CONFIDENCE] * len(contexts)

    total_time = time.time() - st_time
    logger.info(f"Prompt storyGPT exec time: {total_time:.3f}s")
    return jsonify(list(zip(responses, confidences)))
