import logging
import os
from flask import Flask, request, jsonify
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from wiki_parser import wp_call

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
sentry_sdk.init(dsn=os.getenv('SENTRY_DSN'), integrations=[FlaskIntegration()])

app = Flask(__name__)


@app.route("/model", methods=['POST'])
def respond():
    inp = request.json
    parser_info = inp.get("parser_info", [" "])
    query = inp.get("query", [" "])
    res = [[] for _ in query]
    try:
        res = wp_call(parser_info, query)
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)

    return jsonify(res)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
