import logging
import time
import os

from utils import QGTokenizer

import torch
from transformers import T5Config, T5ForConditionalGeneration
from flask import Flask, request, jsonify
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(dsn=os.getenv('SENTRY_DSN'), integrations=[FlaskIntegration()])


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_PATH = os.environ.get('MODEL_PATH', '/data/model.pth')
BASE_MODEL = os.environ.get('BASE_MODEL', 't5-base')
DECODING = os.environ.get('DECODING', 'greedy')  # greedy, topk-N (e.g., topk-10)

cuda = torch.cuda.is_available()
if cuda:
    torch.cuda.set_device(0)  # singe gpu
    device = torch.device('cuda')
else:
    device = torch.device('cpu')

logger.info(f'question generation is set to run on {device}')

# init model
logger.info('question generation model is preparing...')
config = T5Config.from_pretrained(BASE_MODEL)
model = T5ForConditionalGeneration(config=config)
t = QGTokenizer(tokenizer=BASE_MODEL)
checkpoint = torch.load(MODEL_PATH, map_location=device)
model.load_state_dict(checkpoint["model_state_dict"])
model.eval()
if cuda:
    model.cuda()

logger.info(f'question generation model is ready')

app = Flask(__name__)


@app.route("/question", methods=['POST'])
def respond():
    st_time = time.time()

    text = request.json['text']
    answer = request.json['answer']
    sample = {'text': text, 'answer': answer}
    input_ids = t(sample)['input_ids']
    input_ids_t = torch.tensor([input_ids]).to(device)
    if DECODING == 'greedy':
        question = model.generate(input_ids_t, max_length=t.max_tgt_len)[0]
    elif 'topk-' in DECODING:
        k = int(DECODING.split('-')[1])
        question = model.generate(input_ids_t, top_k=k, do_sample=True, max_length=t.max_tgt_len)[0]
    else:
        raise RuntimeError(f'Unknown decoding algo: {DECODING}')
    question = t.tokenizer.decode(question)
    question = question.replace('<pad>', '').replace('question:', '').replace('</s>', '').strip()

    logger.info(question)
    total_time = time.time() - st_time
    logger.info(f'question generation exec time: {total_time:.3f}s')
    return jsonify({'question': question})
