import logging
import time
import os
import re
from functools import lru_cache

import torch
from flask import Flask, request, jsonify
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

import src.data.config as cfg
import src.interactive.functions as interactive

sentry_sdk.init(dsn=os.getenv('SENTRY_DSN'), integrations=[FlaskIntegration()])


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

device = os.environ.get('DEVICE', 'cpu')
graph = os.environ.get('GRAPH', 'atomic')

logger.info(f'comet is set to run on {device} with {graph} graph')

model_file = f'pretrained_models/{graph}_pretrained_model.pickle'

# decoding algorithm should be one of:
# beam-N, e.g., beam-5
# topk-K, e.g., topk-5, topk-1 == greedy
# otherwise -- greedy decoding
decoding_algorithm = os.environ.get('DECODING_ALGO', 'greedy')
logger.info(f'comet decoding algo: {decoding_algorithm}')
default_category = "all"

logger.info('comet model is preparing...')
opt, state_dict = interactive.load_model_file(model_file)
data_loader, text_encoder = interactive.load_data(graph, opt)

if graph == 'atomic':
    n_ctx = data_loader.max_event + data_loader.max_effect
elif graph == 'conceptnet':
    n_ctx = data_loader.max_e1 + data_loader.max_e2 + data_loader.max_r
else:
    raise RuntimeError('Graph {graph} is not in ["atomic", "conceptnet"]')

n_vocab = len(text_encoder.encoder) + n_ctx
model = interactive.make_model(opt, n_vocab, n_ctx, state_dict)

if device != "cpu":
    cfg.device = int(device.split('_')[-1])
    cfg.do_gpu = True
    torch.cuda.set_device(cfg.device)
    model.cuda(cfg.device)
else:
    cfg.device = "cpu"

sampler = interactive.set_sampler(opt, decoding_algorithm, data_loader)


@lru_cache(maxsize=2**16)
def get_comet_atomic_output(input_event, category):
    return interactive.get_atomic_sequence(input_event, model, sampler, data_loader, text_encoder, category)


@lru_cache(maxsize=2**16)
def get_comet_conceptnet_output(input_event, category):
    return interactive.get_conceptnet_sequence(input_event, model, sampler, data_loader, text_encoder, category)


logger.info(f'comet model for {graph} is ready')


other_symbols_compiled = re.compile(r"[^a-zA-Z0-9\- ]")
none_compiled = re.compile(r"\bnone\b", re.IGNORECASE)


def cleanup(text):
    cleaned = re.sub(other_symbols_compiled, "", text)
    cleaned = re.sub(none_compiled, "", cleaned)
    return cleaned.strip()


app = Flask(__name__)


@app.route("/comet", methods=['POST'])
def respond():
    """
    Runs graph predictions with COMeT, supports ATOMIC and ConceptNet
    ATOMIC graph:
        sample request:
            curl --header "Content-Type: application/json" \
            --request POST \
            --data '{"input": "PersonX went to a mall", "category": "xWant"}' \
            http://0.0.0.0:8053/comet

        sample response:
        {
            "xWant": {
                "beams": [
                    "to buy something",
                    "to go home",
                    "to buy things",
                    "to shop",
                    "to go to the store"
                ],
                "effect_type": "xWant",
                "event": "PersonX went to a mall"
            }
        }

    ConceptNet graph:
    works best if words are lemmatized
    sample request:
            curl --header "Content-Type: application/json" \
            --request POST \
            --data '{"input": "go on a hike", "category": "MotivatedByGoal"}' \
            http://0.0.0.0:8065/comet

        sample response:
        {
            "MotivatedByGoal": {
            "beams": [
                "exercise",
                "it be fun",
                "you like hike",
                "you enjoy hike",
                "explore"
            ],
            "relation": "MotivatedByGoal",
            "e1": "go on a hike"
            }
        }

    if `category` is not set then `all` is used.
    """
    st_time = time.time()
    input_event = request.json['input']
    category = request.json.get('category', default_category)

    if isinstance(category, list):
        category = tuple(category)

    if graph == 'atomic':
        output = get_comet_atomic_output(input_event, category)
    elif graph == 'conceptnet':
        output = get_comet_conceptnet_output(input_event, category)
    else:
        raise RuntimeError('Graph {graph} is not in ["atomic", "conceptnet"]')

    for rel in output:
        output[rel]["beams"] = [cleanup(b) for b in output[rel].get('beams', []) if len(cleanup(b)) > 0]

    logger.info(output)
    total_time = time.time() - st_time
    logger.info(f'comet exec time: {total_time:.3f}s')
    return jsonify(output)


def atomic_annotator():
    raise NotImplementedError


def conceptnet_annotator(request, category=("SymbolOf", "HasProperty", "Causes", "CausesDesire")):
    batch = []
    for nounphrases in request['nounphrases']:
        result = {}
        for np in nounphrases:
            cn_result = get_comet_conceptnet_output(np, category=category)
            np_conceptnet_rels = {}
            for rel in cn_result:
                np_conceptnet_rels[rel] = [cleanup(b) for b in cn_result[rel].get('beams', []) if len(cleanup(b)) > 0]
            result[np] = np_conceptnet_rels
        batch += [result]
    return batch


if graph == 'atomic':
    annotator_fn = atomic_annotator
elif graph == 'conceptnet':
    annotator_fn = conceptnet_annotator
else:
    raise RuntimeError('Graph {graph} is not in ["atomic", "conceptnet"]')


@app.route("/comet_annotator", methods=['POST'])
def annotator_respond():
    st_time = time.time()
    output = annotator_fn(request.json)
    logger.info(output)
    total_time = time.time() - st_time
    logger.info(f'comet_{graph}_annotator exec time: {total_time:.3f}s')
    return jsonify(output)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
