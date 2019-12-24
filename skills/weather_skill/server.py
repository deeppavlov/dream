#!/usr/bin/env python

import logging
import time
from os import getenv

import sentry_sdk
from flask import Flask, request, jsonify
# from scenario import MovieSkillScenario
from weather_skill import WeatherSkill

sentry_sdk.init(getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

ws = WeatherSkill()


@app.route("/respond", methods=['POST'])
def respond():
    st_time = time.time()
    dialogs = request.json['dialogs']

    responses, confidences, human_attributes, bot_attributes, attributes = ws(dialogs)
    logger.info(responses)
    total_time = time.time() - st_time
    logger.info(f'weather_skill exec time: {total_time:.3f}s')
    return jsonify(list(zip(responses, confidences, human_attributes, bot_attributes, attributes)))


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
