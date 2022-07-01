import logging
import time
import os

import sentry_sdk
import torch
from flask import Flask, request, jsonify
from sentry_sdk.integrations.flask import FlaskIntegration
from transformers import AutoModelForCausalLM, AutoTokenizer

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

PRETRAINED_MODEL_NAME_OR_PATH = os.environ.get("PRETRAINED_MODEL_NAME_OR_PATH")
logging.info(f"PRETRAINED_MODEL_NAME_OR_PATH = {PRETRAINED_MODEL_NAME_OR_PATH}")
DEFAULT_CONFIDENCE = 0.9
ZERO_CONFIDENCE = 0.0

try:
    tokenizer = AutoTokenizer.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH)
    model = AutoModelForCausalLM.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH)
    if torch.cuda.is_available():
        model.to("cuda")
        logger.info("storygpt is set to run on cuda")
    tokenizer.add_tokens(['<EOT>', '<EOL>'], special_tokens=True)
    tokenizer.add_special_tokens({'pad_token': '[PAD]'})
    model.resize_token_embeddings(len(tokenizer))
    model.load_state_dict(torch.load('/data/filtered_ROCStories_gpt_medium.pt', map_location=torch.device('cpu')))
    # model.load_state_dict(torch.load('filtered_ROCStories_gpt_medium.pt', map_location=torch.device('cpu')))

    logger.info("storygpt is ready")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel("WARNING")


def glue_keywords(keywords):
    dif = len(keywords) - 5
    batches = []
    tmp = []
    c = 0
    for i in range(dif + 1):
        c += 1
        tmp.append(keywords[i])
        if c >= 3:
            batches.append(tmp)
            tmp = []
            c = 0
    batches.append(tmp)
    leftovers = [[k] for k in keywords[dif + 1:]]
    batches.extend(leftovers)
    return [' '.join(keys) for keys in batches]


def generate_response(context, model, tokenizer):
    keywords = context[0]

    if len(keywords) > 5:
        keywords = glue_keywords(keywords)
    logger.info(f"Keywords: {keywords}")

    format_line = '{} <EOT> i {} <EOL>'
    input_line = format_line.format(keywords[0], ' # '.join(keywords))
    logger.info(f"Formatted storyline: {input_line}")

    tmp_prompt = input_line
    input_ids = tokenizer.encode(tmp_prompt, return_tensors="pt")

    with torch.no_grad():
        if torch.cuda.is_available():
            input_ids = input_ids.to("cuda")
        chat_history_ids = model.generate(
            input_ids, do_sample=True, max_length=150, temperature=0.8, top_k=20, top_p=0.9,
            pad_token_id=tokenizer.eos_token_id, no_repeat_ngram_size=3
        )
        if torch.cuda.is_available():
            chat_history_ids = chat_history_ids.cpu()
    result = tokenizer.decode(chat_history_ids[:, input_ids.shape[-1]:][0])
    logger.info(f"Generated from storyline: {result}")
    reply = result.split('<EOL>')[-1].replace('<|endoftext|>', '')
    return reply


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    contexts = request.json.get("utterances_histories", [])

    try:
        responses = []
        confidences = []
        for context in contexts:
            response = generate_response(context, model, tokenizer)
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
