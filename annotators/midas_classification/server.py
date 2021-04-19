import logging
import time
import os

import numpy as np
import sentry_sdk
from deeppavlov import build_model
from flask import Flask, request, jsonify

sentry_sdk.init(os.getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

EMPTY_SIGN = ': EMPTY >'

try:
    model = build_model("midas_conv_bert.json", download=True)
    m = model(['hi'])
except Exception as e:
    logger.exception('Midas not loaded')
    sentry_sdk.capture_exception(e)
    raise e


label_to_act = {0: "opinion", 1: "pos_answer", 2: "statement", 3: "neg_answer", 4: "yes_no_question",
                5: "other_answers", 6: "open_question_factual", 7: "open_question_opinion"}
logger.info(f"Considered classes dictionary: {label_to_act}")


def predict(inputs):
    logger.info(f'Inputs {inputs}')
    if len(inputs) == 1 and inputs[0].strip() == EMPTY_SIGN:
        logger.warning('Calling MIDAS with empty inputs. Check out why')
        return {}
    try:
        predictions = model(inputs)
        responses = [
            {class_name: pred_value.astype(np.float64)
             for class_name, pred_value in zip(label_to_act.values(), preds)}
            for preds in predictions]
    except Exception as e:
        responses = [{class_name: 0 for class_name in label_to_act.values()}
                     for _ in inputs]
        sentry_sdk.capture_exception(e)
        logger.exception(e)
    return responses


@app.route("/model", methods=['POST'])
def respond():
    st_time = time.time()
    inputs = []
    for dialog in request.json.get('dialogs', [{}]):
        if dialog.get('bot_utterances', []):
            prev_bot_uttr_text = dialog["bot_utterances"][-1].get("text", "").lower()
        else:
            prev_bot_uttr_text = ""
        if dialog.get('human_utterances', []):
            curr_human_uttr_text = dialog["human_utterances"][-1].get("text", "").lower()
        else:
            curr_human_uttr_text = ""

        input_ = f"{prev_bot_uttr_text} {EMPTY_SIGN} {curr_human_uttr_text}"
        inputs.append(input_)
    responses = predict(inputs)
    logging.info(f'midas_classification exec time {time.time() - st_time}')
    return jsonify(responses)


@app.route("/batch_model", methods=['POST'])
def batch_respond():
    st_time = time.time()
    bot_utterances = request.json.get('sentences', [""])
    human_utterances = request.json.get('last_human_utterances', [""])
    inputs = [f"{context.lower()} {EMPTY_SIGN} {utterance.lower()}"
              for context, utterance in zip(human_utterances, bot_utterances)]
    responses = predict(inputs)
    logging.info(f'midas_classification exec time {time.time() - st_time}')
    return jsonify([{"batch": responses}])


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
