import logging
import time
import os

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
logger.info(f'comet is set to run on {device}')

model_file = 'pretrained_models/atomic_pretrained_model.pickle'
beam_size = 5
sampling_algorithm = f'beam-{beam_size}'
default_category = "all"

logger.info('comet model is preparing...')
opt, state_dict = interactive.load_model_file(model_file)
data_loader, text_encoder = interactive.load_data("atomic", opt)
n_ctx = data_loader.max_event + data_loader.max_effect
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
logger.info('comet model is ready')

app = Flask(__name__)


@app.route("/comet", methods=['POST'])
def respond():
    """
    Runs ATOMIC graph predictions with COMeT
    sample request:
        curl --header "Content-Type: application/json" \
        --request POST \
        --data '{"input_event":"PersonX went to a mall", "category": "xWant"}' \
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

    if `category` is not set then `all` is used.
    """
    st_time = time.time()
    input_event = request.json['input_event']
    category = request.json.get('category', default_category)
    output = interactive.get_atomic_sequence(input_event, model, sampler, data_loader, text_encoder, category)
    logger.info(output)
    total_time = time.time() - st_time
    logger.info(f'comet exec time: {total_time:.3f}s')
    return jsonify(output)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
