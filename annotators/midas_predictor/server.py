import logging
import time
import uuid
from os import getenv

import sentry_sdk
from flask import Flask, jsonify, request
from sentry_sdk.integrations.logging import ignore_logger

import test_server


ignore_logger("root")
sentry_sdk.init(getenv("SENTRY_DSN"))
app = Flask(__name__)
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)




logger.info(f"midas-predictor is loaded")


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    user_sentences = request.json["sentences"]
    session_id = uuid.uuid4().hex

    sentseg_result = []
    # Only for user response delete alexa from sentence TRELLO#275
    if len(user_sentences) % 2 == 1:
        user_sent_without_alexa = re.sub(r"(^alexa\b)", "", user_sentences[-1], flags=re.I).strip()
        if len(user_sent_without_alexa) > 1:
            user_sentences[-1] = user_sent_without_alexa

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


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
