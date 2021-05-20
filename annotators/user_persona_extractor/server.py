#!/usr/bin/env python

import logging
import re
from time import time

from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk
from common.sensitive import is_sensitive_situation
from common.user_persona_extractor import KIDS_WORDS_RE, ADULTS_WORDS_RE


sentry_sdk.init(getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


def extract_age_group(dialog):
    curr_uttr_text = dialog["human_utterances"][-1]["text"]

    if re.search(KIDS_WORDS_RE, curr_uttr_text):
        age_group = "kid"
    elif re.search(ADULTS_WORDS_RE, curr_uttr_text) or is_sensitive_situation(dialog):
        age_group = "adult"
    else:
        age_group = "unknown"
    return age_group


@app.route("/respond", methods=['POST'])
def respond():
    st_time = time()
    dialogs = request.json['dialogs']

    human_attributes = []

    for i, dialog in enumerate(dialogs):
        curr_human_attr = {}

        if curr_human_attr.get("age_group", "unknown") == "unknown":
            curr_human_attr["age_group"] = extract_age_group(dialog)

        human_attributes.append({"human_attributes": curr_human_attr})

    total_time = time() - st_time
    logger.info(f'user-persona-extractor exec time: {total_time:.3f}s')
    return jsonify(human_attributes)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
