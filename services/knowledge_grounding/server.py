import logging
import os
import random
import time

import sentry_sdk
import torch
from flask import Flask, request, jsonify
from parlai.core.script import ParlaiPreloadModelScript
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(dsn=os.getenv('SENTRY_DSN'), integrations=[FlaskIntegration()])


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


cuda = torch.cuda.is_available()
if cuda:
    torch.cuda.set_device(0)  # singe gpu
    device = torch.device('cuda')
else:
    device = torch.device('cpu')

kg_checkpoint_name = os.environ.get("MODEL_CKPT", "1_sent_48_epochs")

logger.info(f'knowledge grounding model {kg_checkpoint_name} is set to run on {device}')

kg_script = ParlaiPreloadModelScript.main(
    task='topical_chat:generator',
    init_model=f"/opt/conda/lib/python3.7/site-packages"
    f"/data/models/topical_chat_blender90_{kg_checkpoint_name}/model.checkpoint",
    model_file=f"/opt/conda/lib/python3.7/site-packages"
    f"/data/models/topical_chat_blender90_{kg_checkpoint_name}/model",
    fp16=False,
    inference='nucleus',
    topp=0.9,
    skip_generation=False,
)

logger.info('knowledge grounding script has loaded the model and is ready')

app = Flask(__name__)


@app.route("/respond", methods=['POST'])
def respond():
    batch = request.json['batch']
    responses = [""]
    random.seed(42)
    st_time = time.time()
    if batch:
        user_inputs = {
            'history': batch[0]['history'].split('\n') if batch[0]['history'] else [''],
            'inputs': []
        }
        for sample in batch:
            user_inputs['inputs'].append(
                {
                    'checked_sentence': sample['checked_sentence'],
                    'knowledge': sample['knowledge'],
                    'text': sample['text']
                }
            )
        try:
            raw_responses = kg_script.run(user_inputs)
            responses = [r['text'] for r in raw_responses]
            logger.info(f'Current sample responses: {responses}')
        except Exception as e:
            sentry_sdk.capture_exception(e)
            logger.exception(e)
    else:
        logger.info('Received empty batch, exiting with empty responses')
    total_time = time.time() - st_time
    logger.info(f'knowledge grounding one batch exec time: {total_time:.3f}s')
    return jsonify(responses)
