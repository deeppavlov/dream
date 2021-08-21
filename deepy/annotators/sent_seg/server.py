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

sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
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


@app.route("/sentseg", methods=["POST"])
def respond():
    st_time = time.time()
    user_sentences = request.json["sentences"]
    session_id = uuid.uuid4().hex

    sentseg_result = []

    for i, text in enumerate(user_sentences):
        if text.strip():
            logger.info(f"user text: {text}, session_id: {session_id}")
            sentseg = model.predict(sess, text)
            sentseg = sentseg.replace(" '", "'")
            sentseg = preprocessing(sentseg)
            segments = split_segments(sentseg)
            sentseg_result += [{"punct_sent": sentseg, "segments": segments}]
            logger.info(f"punctuated sent. : {sentseg}")
        else:
            sentseg_result += [{"punct_sent": "", "segments": [""]}]
            logger.warning(f"empty sentence {text}")
    total_time = time.time() - st_time
    logger.info(f"sentseg exec time: {total_time:.3f}s")
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


def preprocessing(sentence):
    sentence = sentence.replace(" ai n't", " is not")
    sentence = sentence.replace(" n't", " not")
    sentence = sentence.replace("'m ", " am ")
    sentence = sentence.replace("'re ", " are ")
    sentence = sentence.replace("'ve ", " have ")
    sentence = sentence.replace("'ll ", " will ")
    sentence = sentence.replace("she's ", "she is ")
    sentence = sentence.replace("he's ", "he is ")
    sentence = sentence.replace("it's ", "it is ")
    sentence = sentence.replace("that's ", "that is ")
    sentence = sentence.replace("y'all ", "you all ")
    sentence = sentence.replace("yall ", "you all ")
    sentence = sentence.replace("'d like ", " would like ")
    sentence = sentence.replace(" gon na ", " going to ")
    sentence = sentence.replace(" wan na ", " want to ")
    return sentence


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
