import re
from flask import Flask, jsonify, request
import sentsegmodel as model
import tensorflow as tf
import json
import uuid
import logging
import time
from os import getenv
import sentry_sdk

sentry_sdk.init(getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class pars:
    def __init__(self, dict_properties):
        for k, v in dict_properties.items():
            setattr(self, k, v)


dict_params = json.load(open("config.json"))
params = pars(dict_params)

model = model.model(params)

saver = tf.train.Saver()
sess = tf.Session()
saver.restore(sess, params.model_path)
logger.info("sentseg model is loaded.")

app = Flask(__name__)


@app.route('/sentseg', methods=['POST'])
def respond():
    st_time = time.time()
    user_sentences = request.json['sentences']
    session_id = uuid.uuid4().hex

    sentseg_result = []

    for i, text in enumerate(user_sentences):
        logger.info(f"user text: {text}, session_id: {session_id}")
        sentseg = model.predict(sess, text)
        segments = split_segments(sentseg)
        sentseg_result += [{"punct_sent": sentseg, "segments": segments}]
        logger.info(f"punctuated sent. : {sentseg}")
    total_time = time.time() - st_time
    logger.info(f'sentseg exec time: {total_time:.3f}s')
    return jsonify(sentseg_result)


def split_segments(sentence):
    segm = re.split(r"([\.\?\!])", sentence)
    segm = [sent.strip() for sent in segm if sent != ""]

    curr_sent = ""
    punct_occur = False
    segments = []

    for s in segm:
        if re.match(r"[\.\?\!]", s):
            punct_occur = True
            curr_sent += s
        elif punct_occur:
            segments.append(curr_sent)
            curr_sent = s
            punct_occur = False
        else:
            curr_sent += s
    segments.append(curr_sent)
    return segments


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
