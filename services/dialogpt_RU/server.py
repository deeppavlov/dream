import logging
import time
import os
import random

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from flask import Flask, request, jsonify
from healthcheck import HealthCheck
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

PRETRAINED_MODEL_NAME_OR_PATH = os.environ.get(
    "PRETRAINED_MODEL_NAME_OR_PATH", "DeepPavlov/rudialogpt3_medium_based_on_gpt2_v2"
)
logger.info(f"PRETRAINED_MODEL_NAME_OR_PATH = {PRETRAINED_MODEL_NAME_OR_PATH}")

cuda = torch.cuda.is_available()
if cuda:
    torch.cuda.set_device(0)
    device = "cuda"
else:
    device = "cpu"

try:
    tokenizer = AutoTokenizer.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH)
    model = AutoModelForCausalLM.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH).to(device)
    model.eval()

    logger.info("dialogpt model is ready")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

logger.info(f"dialogpt is set to run on {device}")

SHORT_UTTERANCE_PROBA = 0.7
CONTEXT_DEPTH = 3

params_default = {
    "max_length": 128,
    "no_repeat_ngram_size": 3,
    "do_sample": True,
    "top_k": 20,
    "top_p": 0.9,
    "temperature": 0.7,
    "num_return_sequences": 3,
    "device": device,
    "is_always_use_length": True,
}


def inputs_by_length(input_: dict, length_rep=None):
    if length_rep is None:
        length_rep = len(tokenizer.encode(input_["text"]))
    if params_default["is_always_use_length"]:
        if length_rep <= 15:
            length_param = "1"
        elif length_rep <= 50:
            length_param = "2"
        elif length_rep <= 256:
            length_param = "3"
        else:
            length_param = "-"
    else:
        length_param = "-"
    return f"|{input_['speaker']}|{length_param}|{input_['text']}"


def format_dialogue_with_target(context, context_lengths, context_depth=3, encode=False, tokenizer=None):
    """
    THE LAST UTTERANCE IN THE CONTEXT IS TARGET BOT'S UTTERANCE

    context: List(dict)
    context = [
        {"text": "speaker": "human"},
        {"text": "hi there", "speaker": "bot"},
        {"text": "how are you", "speaker": "human"},
        {"text": "great how are u", "speaker": "bot"},
    ]
    OR
    context = [
        "hi",
        "hi there",
        "how are you",
        "great how are u"
    ]
    """
    if len(context) > 0 and isinstance(context[0], str):
        context_len = len(context)
        # the last uttr is from BOT
        inputs = [{"text": uttr, "speaker": (context_len - uttr_id) % 2} for uttr_id, uttr in enumerate(context)]
        inputs = inputs[-context_depth:]
    else:
        inputs = [{"text": uttr["text"], "speaker": 1 if uttr["speaker"] == "bot" else 0} for uttr in context]
        inputs = inputs[-context_depth:]

    inputs_text = "".join([inputs_by_length(input_, inp_len) for input_, inp_len in zip(inputs, context_lengths)])

    if encode:
        # if encode, return encoded context
        inputs_token_ids = tokenizer.encode(inputs_text, return_tensors="pt")
        return inputs_token_ids

    return inputs_text


def format_dialogue_for_inference(context, context_depth=4, encode=False, tokenizer=None):
    """
    THE LAST UTTERANCE IN THE CONTEXT IS TARGET HUMAN'S UTTERANCE

    context: List(dict)
    context = [
        {"text": "speaker": "human"},
        {"text": "hi there", "speaker": "bot"},
        {"text": "how are you", "speaker": "human"},
    ]
    OR
    context = [
        "hi",
        "hi there",
        "how are you",
    ]
    """
    if len(context) > 0 and isinstance(context[0], str):
        context_len = len(context)
        # the last uttr is from HUMAN
        inputs = [{"text": uttr, "speaker": (context_len - uttr_id - 1) % 2} for uttr_id, uttr in enumerate(context)]
        inputs = inputs[-context_depth:]
    else:
        inputs = [{"text": uttr["text"], "speaker": 1 if uttr["speaker"] == "bot" else 0} for uttr in context]
        inputs = inputs[-context_depth:]

    inputs_text = "".join([inputs_by_length(input_) for input_ in inputs])
    length = "2" if random.uniform(0, 1) > SHORT_UTTERANCE_PROBA else "1"
    inputs_text += f"|1|{length}|"

    if encode:
        # if encode, return encoded context
        inputs_token_ids = tokenizer.encode(inputs_text, return_tensors="pt")
        return inputs_token_ids

    return inputs_text


app = Flask(__name__)
health = HealthCheck(app, "/healthcheck")
logging.getLogger("werkzeug").setLevel("WARNING")


def generate(context, num_return_sequences, context_depth):
    bot_input_ids = format_dialogue_for_inference(
        context, context_depth=context_depth, encode=True, tokenizer=tokenizer
    )
    bot_input_ids = bot_input_ids.to(device)
    params_default["num_return_sequences"] = num_return_sequences

    chat_history_ids = model.generate(bot_input_ids, pad_token_id=tokenizer.eos_token_id, **params_default)
    resp_tokens = chat_history_ids[:, bot_input_ids.shape[-1] :]
    outputs = [tokenizer.decode(x, skip_special_tokens=True) for x in resp_tokens]
    outputs = [x.split("|")[0] for x in outputs]

    return outputs


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()

    dialog_contexts = request.json.get("dialog_contexts", [])
    num_return_sequences = request.json.get("num_return_sequences", 3)

    try:
        batch_generated_responses = []
        for context in dialog_contexts:
            # context is a list of dicts, each dict contains text and speaker label
            # context = [{"text": "utterance text", "speaker": "human"}, ...]
            logger.info(f"dialogpt inputs: {context[-CONTEXT_DEPTH:]}")

            hypotheses = generate(
                context[-CONTEXT_DEPTH:], num_return_sequences=num_return_sequences, context_depth=CONTEXT_DEPTH
            )
            logger.info(f"dialogpt hypotheses: {hypotheses}")
            batch_generated_responses.append(hypotheses)

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        batch_generated_responses = [[]] * len(dialog_contexts)

    total_time = time.time() - st_time
    logger.info(f"dialogpt exec time: {total_time:.3f}s")

    return jsonify({"generated_responses": batch_generated_responses})
