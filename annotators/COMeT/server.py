import logging
import time
import os
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
beam_size = 5
sampling_algorithm = f'beam-{beam_size}'
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

sampler = interactive.set_sampler(opt, sampling_algorithm, data_loader)


@lru_cache(maxsize=2**16)
def get_comet_atomic_output(input_event, category):
    return interactive.get_atomic_sequence(input_event, model, sampler, data_loader, text_encoder, category)


@lru_cache(maxsize=2**16)
def get_comet_conceptnet_output(input_event, category):
    return interactive.get_conceptnet_sequence(input_event, model, sampler, data_loader, text_encoder, category)


logger.info(f'comet model for {graph} is ready')

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

    if graph == 'atomic':
        output = get_comet_atomic_output(input_event, category)
    elif graph == 'conceptnet':
        output = get_comet_conceptnet_output(input_event, category)
    else:
        raise RuntimeError('Graph {graph} is not in ["atomic", "conceptnet"]')

    logger.info(output)
    total_time = time.time() - st_time
    logger.info(f'comet exec time: {total_time:.3f}s')
    return jsonify(output)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
