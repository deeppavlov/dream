import logging
import os

import sentry_sdk
from flask import Flask, jsonify, request
from sentry_sdk.integrations.flask import FlaskIntegration

# logging here because it conflicts with tf
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

import tensorflow as tf  # noqa: E402 cause of logger configuration
from detector import RegMD  # noqa: E402

sentry_sdk.init(dsn=os.getenv('SENTRY_DSN'), integrations=[FlaskIntegration()])


logger = logging.getLogger(__name__)
sess = tf.compat.v1.Session()

logger.info('Creating detector...')

detector = RegMD(logger)
logger.info('Creating detector... finished')

logger.info('Initializing tf variables...')
sess.run(tf.compat.v1.tables_initializer())

logger.info("Tables initialized")
sess.run(tf.compat.v1.global_variables_initializer())
logger.info("Global variables initialized")

detector.detect([["Wake up phrase"]], sess)
logger.info("DONE")

app = Flask(__name__)


@app.route("/detect", methods=['POST'])
def detect():
    utterances = request.json['sentences']
    logger.info(f"Number of utterances: {len(utterances)}")
    results = detector.detect(utterances, sess)
    return jsonify(results)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8014)
    sess.close()
