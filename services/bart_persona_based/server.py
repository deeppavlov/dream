import logging
import os
import time
from typing import List

import sentry_sdk
import torch
from flask import Flask, request, jsonify
from sentry_sdk.integrations.flask import FlaskIntegration

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from common.utils import get_intents
from bart_utils.bot_utils import DialogBotV2, H2PersonaChatHyperparametersV1


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

logging.getLogger("werkzeug").setLevel("INFO")
app = Flask(__name__)

PRETRAINED_MODEL_NAME_OR_PATH = os.environ.get("PRETRAINED_MODEL_NAME_OR_PATH")
PAIR_DIALOG_HISTORY_LENGTH = int(os.environ.get("PAIR_DIALOG_HISTORY_LENGTH", 3))

SUPER_CONFIDENCE = 1.0
DEFAULT_CONFIDENCE = 0.9


try:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"bart_persona_based device: {device}")
    model = AutoModelForSeq2SeqLM.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH)
    model.to(device)
    model.eval()

    tokenizer = AutoTokenizer.from_pretrained(PRETRAINED_MODEL_NAME_OR_PATH)

    if torch.cuda.is_available():
        model.half()

    hyperparameters = H2PersonaChatHyperparametersV1(
        chat_history_pair_length=PAIR_DIALOG_HISTORY_LENGTH,
        persona_max_length=14,
        chat_max_length=25,
        model_name="facebook/bart-base",
    )

    logger.info("bart_persona_based is ready")

except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e


def generate_response(
    persona: List[str] = None,
    model=None,
    tokenizer=None,
    utterances_histories=None,
):
    """generates the next replica of the bot based on a short persona consisting of several sentences.

    Args:
        persona (List[List[str], float]): Top sentences similar to the last replica. Defaults to None.
        model (AutoModelForCausalLM): gpt model. Defaults to None.
        tokenizer (AutoTokenizer): gpt tokenizer. Defaults to None.
        utterances_histories (List[List[str]]): dialog history. Defaults to None.

    Returns:
        str: next utterance
    """

    history = utterances_histories[-PAIR_DIALOG_HISTORY_LENGTH:]
    persona_bot = DialogBotV2(
        model=model,
        tokenizer=tokenizer,
        hyperparameters=hyperparameters,
        history=history,
        persona=persona,
        device=device,
    )

    response = persona_bot.next_response()
    logger.info(f"response: {response}")

    return response


@app.route("/respond", methods=["POST"])
def respond():
    start_time = time.time()
    responses = []
    confidences = []

    last_annotated_utterances_batch = request.json["last_annotated_utterances"]
    utterances_histories = request.json["utterances_histories"]
    try:
        for utterance, utterence_hist in zip(last_annotated_utterances_batch, utterances_histories):
            persona = utterance.get("annotations", {}).get("relative_persona_extractor", [])
            
            response = generate_response(
                model=model,
                tokenizer=tokenizer,
                persona=persona,
                utterances_histories=utterence_hist,
            )

            if "open_question_personal" in get_intents(utterance):
                logger.info("open_question_personal")
                responses.append([response])
                confidences.append([SUPER_CONFIDENCE])
            else:
                logger.info("NOT open_question_personal")
                responses.append([response])
                confidences.append([DEFAULT_CONFIDENCE])

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        responses = [""] * len(last_annotated_utterances_batch)
        confidences = [0.0] * len(last_annotated_utterances_batch)

    total_time = time.time() - start_time
    logger.info(f"bart_persona_based exec time: {total_time:.3f}s")

    return jsonify(list(zip(responses, confidences)))
