#!/usr/bin/env python

from flask import Flask, request, jsonify

import ai
import uuid
import logging


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


app = Flask(__name__)
bot = ai.Chatbot()
bot.initialize("aiml-dir")


@app.route("/respond", methods=['POST'])
def respond():
    # bot.reset() not work
    user_sentences = request.json['sentences']
    response = "..."
    session_id = uuid.uuid4().hex
    logger.info("user_sentences: {}, session_id: {}".format(user_sentences, session_id))
    for s in user_sentences:
        response = bot.respond(s, session_id).replace("\n", "")
    logger.info("response: {}".format(response))
    return jsonify([response])


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
