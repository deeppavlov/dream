import logging
import os
import time
from flask import Flask, request, jsonify
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from wiki_parser import wp_call
from common.utils import remove_punctuation_from_dict_keys


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

app = Flask(__name__)


@app.route("/model", methods=["POST"])
def respond():
    st_time = time.time()
    inp = request.json
    parser_info = inp.get("parser_info", ["find_triplets"])
    query = inp.get("query", [("Q0", "P0", "forw")])
    utt_num = inp.get("utt_num", 0)
    res = [[] for _ in query]
    logger.debug("Calling wp")
    try:
        res = wp_call(parser_info, query, utt_num)
        res = remove_punctuation_from_dict_keys(res)
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
    total_time = time.time() - st_time
    logger.info(f"wiki parser exec time = {total_time:.3f}s")
    return jsonify(res)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
