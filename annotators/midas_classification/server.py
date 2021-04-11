import logging
import time
import os
import numpy as np
from scipy.special import softmax
from simpletransformers.classification import ClassificationModel
import sentry_sdk
from flask import Flask, request, jsonify

sentry_sdk.init(os.getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

MIDAS_DEFAULT_THRESHOLD = 0.01
EMPTY_SIGN = ': EMPTY >'

try:
    model_dir = '/midas'
    model = ClassificationModel(model_type='bert', model_name=model_dir, tokenizer_type='bert',
                                use_cuda=True, num_labels=24, cuda_device=0,
                                args={'sliding_window': True, 'fp16': False, 'reprocess_input_data': True,
                                      'use_multiprocessing': False,
                                      'cache_dir': 'midas',
                                      'best_model_dir': 'midas', 'no_cache': True})
    m = model.predict(['hi'])
except Exception as e:
    logger.exception('Midas not loaded')
    sentry_sdk.capture_exception(e)
    raise e

label_to_act = {0: "statement", 1: "back-channeling", 2: "opinion", 3: "pos_answer", 4: "abandon",
                5: "appreciation", 6: "yes_no_question", 7: "closing", 8: "neg_answer",
                9: "other_answers", 10: "command", 11: "hold", 12: "complaint",
                13: "open_question_factual", 14: "open_question_opinion", 15: "comment",
                16: "nonsense", 17: "dev_command", 18: "correction", 19: "opening", 20: "clarifying_question",
                21: "uncertain", 22: "non_compliant", 23: "open_question_personal"}


def predict(inputs, threshold):
    logger.info(f'Inputs {inputs}')
    if len(inputs) == 1 and inputs[0].strip() == EMPTY_SIGN:
        logger.warning('Calling MIDAS with empty inputs. Check out why')
        return {}
    try:
        predictions, raw_outputs = model.predict(inputs)
        raw_outputs = [raw_output.astype(np.float64) for raw_output in raw_outputs]
        # convert to float64 because float32 is not json serializable
        logger.info(f'predicted raw label is {[label_to_act[k] for k in predictions]}')
        pred_probas = list(map(softmax, raw_outputs))
        responses = [dict(zip(label_to_act.values(), pred[0])) for pred in pred_probas]
        for i in range(len(responses)):
            max_prob = max(responses[i].values())
            for label in label_to_act.values():
                if responses[i][label] < min(threshold, max_prob):
                    del responses[i][label]
        assert len(responses) == len(inputs)
    except Exception as e:
        responses = [{'': 0} for _ in inputs]
        sentry_sdk.capture_exception(e)
        logger.exception(e)
    return responses


@app.route("/model", methods=['POST'])
def respond():
    st_time = time.time()
    inputs = []
    threshold = request.json.get('threshold', MIDAS_DEFAULT_THRESHOLD)
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
    responses = predict(inputs, threshold)
    logging.info(f'midas_classification exec time {time.time() - st_time}')
    return jsonify(responses)


@app.route("/batch_model", methods=['POST'])
def batch_respond():
    st_time = time.time()
    bot_utterances = request.json.get('sentences', [""])
    human_utterances = request.json.get('last_human_utterances', [""])
    threshold = request.json.get('threshold', MIDAS_DEFAULT_THRESHOLD)
    inputs = [f"{context.lower()} {EMPTY_SIGN} {utterance.lower()}"
              for context, utterance in zip(human_utterances, bot_utterances)]
    responses = predict(inputs, threshold)
    logging.info(f'midas_classification exec time {time.time() - st_time}')
    return jsonify([{"batch": responses}])


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
