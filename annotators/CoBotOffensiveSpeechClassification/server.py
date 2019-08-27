#!/usr/bin/env python

import json
import logging
import os
import uuid

import requests
from flask import Flask, request, jsonify

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

COBOT_API_KEY = os.environ.get('COBOT_API_KEY')
COBOT_OFFENSIVE_SERVICE_URL = os.environ.get('COBOT_OFFENSIVE_SERVICE_URL')

if COBOT_API_KEY is None:
    raise RuntimeError('COBOT_API_KEY environment variable is not set')
if COBOT_OFFENSIVE_SERVICE_URL is None:
    raise RuntimeError('COBOT_OFFENSIVE_SERVICE_URL environment variable is not set')

headers = {'Content-Type': 'application/json;charset=utf-8', 'x-api-key': f'{COBOT_API_KEY}'}

toxicity_classes = {0: "non-toxic", 1: "toxic"}
blacklist_classes = {0: "not blacklist", 1: "blacklist"}


@app.route("/offensiveness", methods=['POST'])
def respond():
    user_sentences = request.json['sentences']
    session_id = uuid.uuid4().hex
    blacklists = []
    toxicities = []
    confidences = []
    result = requests.request(url=f'{COBOT_OFFENSIVE_SERVICE_URL}',
                              headers=headers,
                              data=json.dumps({'utterances': user_sentences}),
                              method='POST').json()

    for i, sent in enumerate(user_sentences):
        logger.info(f"user_sentence: {sent}, session_id: {session_id}")
        toxicity = toxicity_classes[result["offensivenessClasses"][i]["values"][1]["offensivenessClass"]]
        confidence = float(result["offensivenessClasses"][i]["values"][1]["confidence"])
        blacklist = blacklist_classes[result["offensivenessClasses"][i]["values"][0]["offensivenessClass"]]
        toxicities += [toxicity]
        confidences += [confidence]
        blacklists += [blacklist]
        logger.info(f"sentiment: {toxicity}")

    return jsonify(list(zip(toxicities, confidences, blacklists)))


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
