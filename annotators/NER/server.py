import logging
import time
from os import getenv

import flair
import sentry_sdk
import torch
from flair.data import Sentence
from flair.models import SequenceTagger
from flask import Flask, jsonify, request

sentry_sdk.init(getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

cuda_available = torch.cuda.is_available()
logger.info(f"torch.cuda.is_available(): {cuda_available}")
DEVICE = getenv("DEVICE", "cpu")
logger.info(f"DEVICE: {DEVICE}")
if torch.cuda.is_available():
    flair.device = torch.device(DEVICE)
    logger.info("set flair.device to cuda")
else:
    logger.info("set flair.device to cpu")
    flair.device = torch.device('cpu')

tagger = SequenceTagger.load('ner-ontonotes')
logger.info("flair model is loaded.")

app = Flask(__name__)


def annotate(list_sents):
    sentences = [Sentence(sent) for sent in list_sents]
    tagger.predict(sentences=sentences, embedding_storage_mode="gpu")
    return [sent.to_dict(tag_type='ner')["entities"] for sent in sentences]


@app.route('/ner', methods=['POST'])
def respond():
    st_time = time.time()
    last_utterances = request.json["last_utterances"]
    logger.info(f"input (the last utterances): {last_utterances}")

    ret = []

    for i, utterance in enumerate(last_utterances):
        ret.append(annotate(utterance))

    logger.info(f"NER output: {ret}")

    total_time = time.time() - st_time
    logger.info(f'NER exec time: {total_time: .3f}s')
    return jsonify(ret)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8021)
