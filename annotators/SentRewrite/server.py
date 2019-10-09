from sentrewrite import recover_mentions
from flask import Flask, jsonify, request
import uuid
import logging
import time
from os import getenv
import sentry_sdk

sentry_sdk.init(getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route('/sentrewrite', methods=['POST'])
def respond():
    st_time = time.time()
    utterances_histories = request.json["utterances_histories"]
    session_id = uuid.uuid4().hex

    logger.info(utterances_histories)

    ret = []

    # utterances_histories: list of dialogs, each dialog is a list of utterances, each utterance is a list of sentences.
    # utterances_histories = [dialogs] -> [utterances] -> [sentences]
    logger.info(f"utterances_histories: {utterances_histories}, session id: {session_id}")
    for i, dialog in enumerate(utterances_histories):
        # keep only 5 latest utterances
        if len(dialog) > 5:
            dialog = dialog[-5:]
        ret.append(recover_mentions(dialog))

    logger.info(f"output: {ret}")
    total_time = time.time() - st_time
    logger.info(f'sent. rewrite exec time: {total_time: .3f}s')

    return jsonify(ret)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
