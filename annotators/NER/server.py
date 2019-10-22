from flair.data import Sentence
from flair.models import SequenceTagger
from flask import Flask, jsonify, request
import logging
import time
from os import getenv
import sentry_sdk

sentry_sdk.init(getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("flair model is loading...")
tagger = SequenceTagger.load('ner-ontonotes')
logger.info("flair model is loaded.")

app = Flask(__name__)


def annotate(sent):
    sentence = Sentence(sent)
    tagger.predict(sentence)
    return sentence.to_dict(tag_type='ner')["entities"]


@app.route('/ner', methods=['POST'])
def respond():
    st_time = time.time()
    last_utterances = request.json["last_utterances"]
    logger.info(f"input (the last utterances): {last_utterances}")

    ret = []

    for i, utterance in enumerate(last_utterances):
        ret.append([])
        for sent in utterance:
            ret[-1].append(annotate(sent))

    logger.info(f"NER output: {ret}")

    total_time = time.time() - st_time
    logger.info(f'NER exec time: {total_time: .3f}s')
    return jsonify(ret)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8021)
