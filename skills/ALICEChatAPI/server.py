#!/usr/bin/env python

from flask import Flask, request, jsonify

import ai
import uuid
import logging
import time

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
bot = ai.Chatbot()
bot.initialize("aiml-dir")


@app.route("/respond", methods=['POST'])
def respond():
    # todo: logging doesn't work here, some problems with Sanic
    st_time = time.time()
    # bot.reset() not work
    responses = []
    for user_sentences in request.json['sentences_batch']:
        response = "..."
        session_id = uuid.uuid4().hex
        logger.info("user_sentences: {}, session_id: {}".format(user_sentences, session_id))
        for s in user_sentences:
            response = bot.respond(s, session_id).replace("\n", "")
        logger.info("response: {}".format(response))
        if response.strip() and "INTERJECTION" not in response:
            confidence = 0.65
        else:
            confidence = 0.
            response = ""
        responses.append([response, confidence])

    total_time = time.time() - st_time
    logger.info(f'alice exec time: {total_time:.3f}s')
    return jsonify(responses)


@app.route("/healthz", methods=['GET'])
def healthz():
    return "OK", 200


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
