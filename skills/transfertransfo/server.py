import logging
import os
import random
import time

import numpy as np
import torch
from pytorch_pretrained_bert import OpenAIGPTLMHeadModel, OpenAIGPTTokenizer
from flask import Flask, request, jsonify
from flasgger import Swagger, swag_from
import sentry_sdk

from infer.utils import create_generator, get_special_tokens_ids
from infer.beamsearch import beam_sampler
from postprocessor.postprocessing import ReplyChecker

# from postprocessor.retrieval import Retrieval
from postprocessor.postprocessing import postprocess_text, DROP_SPEC_TOKEN


# define environment
SENTRY_DSN = os.getenv("SENTRY_DSN")

SEED = 31415
DEVICE = os.getenv("DEVICE", "cpu")  # cuda or cpu
MAX_HISTORY = 2
MAX_LENGTH = 20
MIN_LENGTH = 1
MODEL_PATH = os.getenv("MODEL_PATH", "./models")

MAX_PERSONA_TOKEN_LENGTH = 200
MAX_HISTORY_TOKEN_LENGTH = 200

TOP_K = 10
TOP_P = 0.9
TEMPERATURE = 2.9
NO_SAMPLE = False
BEAM_SIZE = 3
NBEST = 3
NGRAM_SIZE = 3
REPLACE_NGRAM = False

CORRECT_GENERATIVE = True
SPLIT_INTO_SENTENCES = True

ADD_QUESTIONS = 0
EMOJI_PROB = 1
# EMOJI_PROB = 0.3

APPROX_CONF = os.getenv("APPROX_CONF", True)

# init

sentry_sdk.init(SENTRY_DSN)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(module)s %(lineno)d %(levelname)s : %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)
logger.info(DEVICE)

reply_checker = ReplyChecker(
    max_len=BEAM_SIZE, correct_generative=CORRECT_GENERATIVE, split_into_sentences=SPLIT_INTO_SENTENCES
)

app = Flask(__name__)
swagger = Swagger(app)

random.seed(SEED)
torch.random.manual_seed(SEED)
torch.cuda.manual_seed(SEED)


tokenizer = OpenAIGPTTokenizer.from_pretrained(MODEL_PATH)
model = OpenAIGPTLMHeadModel.from_pretrained(MODEL_PATH)

model.to(DEVICE)
model.eval()
generator = create_generator(tokenizer, model, device=DEVICE)


special_tokens_ids = get_special_tokens_ids(tokenizer)

confidences = np.load("confidences.npy")


def check_lenghts(lenghts, max_len):
    return np.flip(np.flip(np.array(lenghts)).cumsum() < max_len).tolist()


def to_ids(personality, utterances_histories):
    personality_ids = [tokenizer.encode(ut) for ut in personality]
    utterances_histories_ids = [tokenizer.encode(ut) for ut in utterances_histories]
    utterances_histories_ids = utterances_histories_ids[-(2 * MAX_HISTORY + 1) :]
    personality_ids = [
        line_ids
        for is_not_overflow, line_ids in zip(
            check_lenghts([len(ids) for ids in personality_ids], MAX_PERSONA_TOKEN_LENGTH), personality_ids
        )
        if is_not_overflow
    ]
    utterances_histories_ids = [
        line_ids
        for is_not_overflow, line_ids in zip(
            check_lenghts([len(ids) for ids in utterances_histories_ids], MAX_HISTORY_TOKEN_LENGTH),
            utterances_histories_ids,
        )
        if is_not_overflow
    ]
    return personality_ids, utterances_histories_ids


# # warmup model
# personality_ids, utterances_histories_ids = to_ids(
#     ["I am a tester of this skill" for _ in range(120)], ["hi tester, how are you" for _ in range(120)]
# )
# generator(personality=personality_ids, history=utterances_histories_ids)


def approximate_confidence(confidence):
    return (confidences < confidence).sum() / len(confidences)


def softmax(x):
    """Compute softmax values for each sets of scores in x."""
    return np.exp(x) / np.sum(np.exp(x), axis=0)


def inference(personality, utterances_histories):
    personality_ids, utterances_histories_ids = to_ids(personality, utterances_histories)

    # reply generation
    with torch.no_grad():
        reply_ids, reply_probs = beam_sampler(
            personality_ids,
            utterances_histories_ids,
            generator,
            special_tokens_ids,
            min_length=MIN_LENGTH,
            max_length=MAX_LENGTH,
            top_k=TOP_K,
            top_p=TOP_P,
            temperature=TEMPERATURE,
            no_sample=NO_SAMPLE,
            beam_size=BEAM_SIZE,
            nbest=NBEST,
        )
    # ids to tokens
    raw_reply_tokens, reply_confidence = list(
        zip(
            *[
                (tokenizer.decode(out_ids, skip_special_tokens=True), out_probs)
                for out_ids, out_probs in zip(reply_ids, reply_probs)
                if out_probs
            ]
        )
    )

    # reply postprocessing
    reply_tokens = [
        postprocess_text(
            reply,
            utterances_histories,
            personality,
            reply_checker,
            add_questions=ADD_QUESTIONS,
            emoji_prob=EMOJI_PROB,
            ngram_size=NGRAM_SIZE,
            replace_ngram=REPLACE_NGRAM,
        )
        for reply in raw_reply_tokens
    ]
    reply_checker.clean()

    # drop bad reply
    best_reply_tokens = [
        (raw, conf)
        for raw, new, conf in zip(raw_reply_tokens, reply_tokens, reply_confidence)
        if not (DROP_SPEC_TOKEN in new)
    ]
    if best_reply_tokens:
        best_reply_tokens, best_reply_confidence = zip(*best_reply_tokens)
    else:
        return "sorry", 0.0

    i = np.random.choice(np.arange(len(best_reply_confidence)), 1, p=softmax(best_reply_confidence))[0]

    return (
        best_reply_tokens[i],
        (approximate_confidence(best_reply_confidence[i]) if APPROX_CONF else best_reply_confidence[i]),
    )


@app.route("/transfertransfo", methods=["POST"])
@swag_from("chitchat_endpoint.yml")
def transfer_transfo_chitchat_model():
    st_time = time.time()
    personality = request.json["personality"]
    utterances_histories = request.json["utterances_histories"]
    response = [inference(pers, hist) for pers, hist in zip(personality, utterances_histories)]
    total_time = time.time() - st_time
    logger.info(f"transfertransfo exec time: {total_time:.3f}s")
    return jsonify(response)
