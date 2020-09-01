import logging
import time
from os import getenv
import sentry_sdk
from flask import Flask, request, jsonify

sentry_sdk.init(getenv('SENTRY_DSN'))


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

logger.info('I am ready to respond')


@app.route("/respond", methods=['POST'])
def respond():
    st_time = time.time()
    sentences = request.json['sentences']
    result = [answer['cobot_dialogact_topics'] for answer in sentences]
    total_time = time.time() - st_time
    logger.info(f'nounphrase annotator exec time: {total_time:.3f}s')
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
