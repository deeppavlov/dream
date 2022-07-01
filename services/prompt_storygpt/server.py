import logging
import time
import os

import sentry_sdk
import torch
from flask import Flask, request, jsonify
from sentry_sdk.integrations.flask import FlaskIntegration
from transformers import GPT2Tokenizer, GPT2LMHeadModel
from transformers import BartForConditionalGeneration, BartTokenizer

import nltk
from nltk.corpus import stopwords
import re
from nltk.tokenize import sent_tokenize

nltk.download('stopwords')
nltk.download('punkt')
stop_words = stopwords.words('english')

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_CONFIDENCE = 0.9
ZERO_CONFIDENCE = 0.0
device = 'cpu'

try:
    tokenizer = GPT2Tokenizer.from_pretrained('/data/finetuned2')
    tokenizer.padding_side = "left"
    tokenizer.pad_token = tokenizer.eos_token
    model = GPT2LMHeadModel.from_pretrained('/data/finetuned2')
    bart_model = BartForConditionalGeneration.from_pretrained("facebook/bart-large", forced_bos_token_id=0)
    bart_tok = BartTokenizer.from_pretrained("facebook/bart-large")
    if torch.cuda.is_available():
        model.to("cuda")
        device = "cuda"
        logger.info("prompt_storygpt is set to run on cuda")
    logger.info("prompt_storygpt is ready")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel("WARNING")


def generate_part(texts, max_len, temp, num_sents, first):
    encoding = tokenizer(texts, padding=True, return_tensors='pt').to(device)
    with torch.no_grad():
        generated_ids = model.generate(**encoding, max_length=max_len, length_penalty=-100.0,
                                       temperature=temp, do_sample=True)
    generated_texts = tokenizer.batch_decode(
        generated_ids, skip_special_tokens=True)

    texts = []
    for text in generated_texts:
        text = re.sub(r'\(.*?\)', '', text)  # delete everything in ()
        text = text.replace(' .', '.').replace('..', '.').replace('..', '.')
        sents = sent_tokenize(text)
        text = text[:len(' '.join(sents[:num_sents]))]
        if text[-1] not in ',.!?;':
            text += '.'
        if first:
            text += " In the end,"
        texts.append(text)
    return texts


def fill_mask(masked_phrase):
    batch = bart_tok(masked_phrase, return_tensors='pt')
    generated_ids = bart_model.generate(batch['input_ids'])
    filled = bart_tok.batch_decode(generated_ids, skip_special_tokens=True)
    logger.info(f'Filled mask: {filled}')
    return filled[0]


def generate_response(context):
    noun = context[-1]
    logger.info(f"Topic in StoryGPT service: {noun}")
    masked = f"Let me share a story about {noun}. I <mask> {noun}"
    filled = fill_mask(masked)
    texts = [filled]
    first_texts = generate_part(texts, 100, 1, 4, first=True)
    logger.info(f"First part generated: {first_texts[0]}")
    final_texts = generate_part(first_texts * 2, 150, 0.8, 5, first=False)
    logger.info(f"Generated: {final_texts[0]}")
    reply = final_texts[0]
    return reply


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    contexts = request.json.get("utterances_histories", [])

    try:
        responses = []
        confidences = []
        for context in contexts:
            response = generate_response(context)
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
    logger.info(f"masked_lm exec time: {total_time:.3f}s")
    return jsonify(list(zip(responses, confidences)))
