import logging
import time
from os import getenv
import en_core_web_sm
import sentry_sdk
from flask import Flask, request, jsonify

#  import spacy - not worked
#  nlp = spacy.load("en_core_web_sm") - not worked
nlp = en_core_web_sm.load()

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
    result = []
    logger.debug(f"Input sentences: {sentences}")
    for sentence in sentences:
        nlp_result = nlp(sentence)
        nounphrases = [j.text for j in nlp_result.noun_chunks]
        result.append(nounphrases)
    logger.debug(f"Output: {result}")
    total_time = time.time() - st_time
    logger.info(f'nounphrase annotator exec time: {total_time:.3f}s')
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
