import logging
import time
from os import getenv

import sentry_sdk
from flask import Flask, request, jsonify
from common.utils import substitute_nonwords

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


def is_asr_trustable(human_utterances, cur_asr_confidence):
    if len(human_utterances) < 2:
        return True

    is_cur_low = cur_asr_confidence == "very_low"
    cur_text = substitute_nonwords(human_utterances[-1]['text'].lower())
    prev_human_utt = substitute_nonwords(human_utterances[-2]['text'].lower())
    is_prev_low = human_utterances[-2]["annotations"].get("asr", {}).get("asr_confidence", "undefined") == "very_low"
    identical_utts = cur_text == prev_human_utt
    both_has_very_low_asr = is_cur_low and is_prev_low
    not_trustable = both_has_very_low_asr or identical_utts
    if not_trustable and is_cur_low:
        return False
    return True


@app.route("/asr_check", methods=['POST'])
def respond():
    st_time = time.time()
    speeches = request.json['speeches']
    human_utterances = request.json['human_utterances']
    result = []
    logger.debug(f"ASR Input speeches: {speeches}")
    for speech, human_utts in zip(speeches, human_utterances):
        if speech_exists(speech):
            text, mean_proba = get_text_from_speech(speech)
            if mean_proba <= 0.1:
                result.append({'asr_confidence': 'very_low'})
            elif mean_proba > 0.1 and mean_proba <= 0.45:
                result.append({'asr_confidence': 'low'})
            elif mean_proba > 0.45 and mean_proba < 0.62:
                result.append({'asr_confidence': 'medium'})
            else:
                result.append({'asr_confidence': 'high'})
        else:
            result.append({'asr_confidence': 'undefined'})
        if not is_asr_trustable(human_utts, result[-1]['asr_confidence']):
            # If two times in a row asr confidence is very low or both user sents are identical
            # it seems like we can't trust asr, so set confidence to undefined
            result[-1]['asr_confidence'] = 'undefined'

    total_time = time.time() - st_time
    logger.info(f'asr annotator exec time: {total_time:.3f}s')
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
