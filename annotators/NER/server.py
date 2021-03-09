import logging
import time
from copy import deepcopy
from os import getenv

import ner_model
import sentry_sdk
from flask import Flask, jsonify, request
from nltk.tokenize import word_tokenize

sentry_sdk.init(getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)

ner = ner_model.load_model()
logger.info("ner model is loaded.")

BANNED_ENTITIES = ["okay", "oh", "name", "ocean", "hey", "cool", "corona"]

with open("./google-english-no-swears.txt", "r") as f:
    UNIGRAMS = set(f.read().splitlines()[:500])


@app.route('/ner', methods=['POST'])
def respond():
    st_time = time.time()
    last_utterances = request.json["last_utterances"]
    logger.info(f"input (the last utterances): {last_utterances}")

    ret = []
    for utterance in last_utterances:
        sents = [word_tokenize(sent.lower()) for sent in utterance]
        preds = ner.predict(sents)
        # each sample is a list of sentences of current utterance
        # so, preds is a list of length = number of sents in utterances
        # each element of preds is a list of entities.
        # EXAMPLE:
        # one sample = ["i have been in london and greece.", "my name is valentine and beatrice."]
        # preds = [[{'confidence': 1, 'end_pos': 5, 'start_pos': 4, 'text': 'london', 'type': 'LOC'},
        #           {'confidence': 1, 'end_pos': 7, 'start_pos': 6, 'text': 'greece', 'type': 'LOC'}],
        #          [{'confidence': 1, 'end_pos': 4, 'start_pos': 3, 'text': 'valentine', 'type': 'PER'},
        #           {'confidence': 1, 'end_pos': 6, 'start_pos': 5, 'text': 'beatrice', 'type': 'PER'}]]
        good_preds = []
        for entities_for_sent in preds:
            good_entities_for_sent = []

            for ent in entities_for_sent:
                ent_text = ent["text"].lower()
                if ent_text not in BANNED_ENTITIES and ent_text not in UNIGRAMS and len(ent_text) > 2:
                    good_entities_for_sent.append(deepcopy(ent))

            good_preds.append(good_entities_for_sent)

        ret.append(good_preds)

    logger.info(f"NER output: {ret}")

    total_time = time.time() - st_time
    logger.info(f'NER exec time: {total_time: .3f}s')
    return jsonify(ret)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8021)
