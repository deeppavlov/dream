#!/usr/bin/env python

import json
import logging
import os
import re
import time
from copy import deepcopy

import requests
from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk


sentry_sdk.init(getenv('SENTRY_DSN'))


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

COBOT_API_KEY = os.environ.get('COBOT_API_KEY')
COBOT_NER_SERVICE_URL = os.environ.get('COBOT_NER_SERVICE_URL')

if COBOT_API_KEY is None:
    raise RuntimeError('COBOT_API_KEY environment variable is not set')
if COBOT_NER_SERVICE_URL is None:
    raise RuntimeError('COBOT_NER_SERVICE_URL environment variable is not set')

headers = {'Content-Type': 'application/json;charset=utf-8', 'x-api-key': f'{COBOT_API_KEY}'}
EVERYTHING_EXCEPT_LETTERS_DIGITALS_AND_SPACE = re.compile(r"[^a-zA-Z0-9 \-&*+]")
DOUBLE_SPACES = re.compile(r"\s+")


@app.route("/entities", methods=['POST'])
def respond():
    st_time = time.time()
    user_utterances = request.json['sentences']
    user_nounphrases = request.json['nounphrases']

    outputs = []

    for i, uttr in enumerate(user_utterances):
        curr_entities = []  # list of string entities, like `"baseball"`
        curr_labelled_entities = []  # list of dictionaries, like `{'text': 'baseball', 'label': 'sport'}`
        try:
            result = requests.request(url=f'{COBOT_NER_SERVICE_URL}',
                                      headers=headers,
                                      data=json.dumps({'input': uttr}),
                                      method='POST',
                                      timeout=0.6)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            logger.exception(e)
            result = requests.Response()
            result.status_code = 504

        if result.status_code != 200:
            msg = "result status code is not 200: {}. result text: {}; result status: {}".format(result, result.text,
                                                                                                 result.status_code)
            sentry_sdk.capture_message(msg)
            logger.warning(msg)
        else:
            result = result.json()
            # {'response': [{'text': 'baseball', 'label': 'sport'},
            #               {'text': 'sportsman', 'label': 'misc'},
            #               {'text': 'michail jordan', 'label': 'person'},
            #               {'text': 'basketballist', 'label': 'sport'}],
            #  'model_version': 'v1.1'}
            if len(result["response"]) >= 2:
                new_result = {"response": []}
                used_ent = False
                for ent_first, ent_next in zip(result["response"][:-1], result["response"][1:]):
                    if f"{ent_first['text']} {ent_next['text']}" in user_nounphrases[i]:
                        if ent_first['label'] == ent_next['label']:
                            new_result["response"] += [{"text": f"{ent_first['text']} {ent_next['text']}",
                                                        "label": ent_next['label']}]
                        else:
                            new_result["response"] += [{"text": f"{ent_first['text']} {ent_next['text']}",
                                                        "label": "misc"}]
                        used_ent = True
                    elif not used_ent:
                        new_result["response"] += [ent_first]
                    else:
                        # this ent was already added
                        used_ent = False
                if result["response"][-1] not in new_result["response"] and \
                        result["response"][-1]["text"] not in new_result["response"][-1]["text"]:
                    new_result["response"] += [result["response"][-1]]
                result["response"] = deepcopy(new_result["response"])

            curr_entities = []
            curr_labelled_entities = []
            for lab_ent in result["response"]:
                lab_ent["text"] = EVERYTHING_EXCEPT_LETTERS_DIGITALS_AND_SPACE.sub(" ", lab_ent["text"])
                lab_ent["text"] = DOUBLE_SPACES.sub(" ", lab_ent["text"]).strip()
                curr_entities += [lab_ent["text"]]
                curr_labelled_entities += [lab_ent]

        outputs.append({"entities": curr_entities, "labelled_entities": curr_labelled_entities})

    total_time = time.time() - st_time
    logger.info(f'cobot_ner exec time: {total_time:.3f}s')
    return jsonify(outputs)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
