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


def get_text_from_speech(speech):
    tokens, probs = zip(*[(token['value'], token['confidence']) for token in speech['hypotheses'][0]['tokens']])
    text = ' '.join(tokens)
    mean_proba = sum(probs) / len(probs)
    return text, mean_proba


def speech_exists(speech):
    if speech and speech['hypotheses']:
        if speech['hypotheses'] and speech['hypotheses'][0].get('tokens'):
            return True
    return False


@app.route("/asr_check", methods=['POST'])
def respond():
    st_time = time.time()
    speeches = request.json['speeches']
    result = []
    logger.debug(f"ASR Input speeches: {speeches}")
    for speech in speeches:
        if speech_exists(speech):
            text, mean_proba = get_text_from_speech(speech)
            if mean_proba <= 0.45:
                result.append({'asr_confidence': 'very_low'})
            elif mean_proba > 0.45 and mean_proba < 0.62:
                result.append({'asr_confidence': 'medium'})
            else:
                result.append({'asr_confidence': 'high'})
        else:
            result.append({'asr_confidence': 'undefined'})

    total_time = time.time() - st_time
    logger.info(f'asr annotator exec time: {total_time:.3f}s')
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
