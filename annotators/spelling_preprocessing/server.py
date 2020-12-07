import logging
import re
import time
from os import getenv

import sentry_sdk
from deeppavlov import build_model
from flask import Flask, request, jsonify

sentry_sdk.init(getenv('SENTRY_DSN'))


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

SPELL_CHECK_MODEL = build_model(config="brillmoore_wikitypos_en")

templates = []
templates += [(re.compile(r"\bwon'?t\b", flags=re.IGNORECASE), "will not")]
templates += [(re.compile(r"\bhaven'?t\b", flags=re.IGNORECASE), "have not")]
templates += [(re.compile(r"\bhadn'?t\b", flags=re.IGNORECASE), "had not")]
templates += [(re.compile(r"\bdoesn'?t\b", flags=re.IGNORECASE), "does not")]
templates += [(re.compile(r"\bdon'?t\b", flags=re.IGNORECASE), "do not")]
templates += [(re.compile(r"\bdidn'?t\b", flags=re.IGNORECASE), "did not")]
templates += [(re.compile(r"\bcan'?t\b", flags=re.IGNORECASE), "can not")]
templates += [(re.compile(r"\bi'?m\b", flags=re.IGNORECASE), "i am")]
templates += [(re.compile(r"\bisn'?t\b", flags=re.IGNORECASE), "is not")]
templates += [(re.compile(r"\baren'?t\b", flags=re.IGNORECASE), "are not")]
templates += [(re.compile(r"\bi'd\b", flags=re.IGNORECASE), "i would")]

templates += [(re.compile(r"\bu\b", flags=re.IGNORECASE), "you")]
templates += [(re.compile(r"\br\b", flags=re.IGNORECASE), "are")]
templates += [(re.compile(r"\bya\b", flags=re.IGNORECASE), "you")]
templates += [(re.compile(r"\bem\b", flags=re.IGNORECASE), "them")]
templates += [(re.compile(r"\bda\b", flags=re.IGNORECASE), "the")]
templates += [(re.compile(r"\bain't\b", flags=re.IGNORECASE), "is not")]
templates += [(re.compile(r"\bur\b", flags=re.IGNORECASE), "your")]
templates += [(re.compile(r"\bru\b", flags=re.IGNORECASE), "are you")]
templates += [(re.compile(r"\burs\b", flags=re.IGNORECASE), "yours")]
templates += [(re.compile(r"\byou'?re\b", flags=re.IGNORECASE), "you are")]

templates += [(re.compile(r"\byall\b", flags=re.IGNORECASE), "you all")]
templates += [(re.compile(r"\by'all\b", flags=re.IGNORECASE), "you all")]
templates += [(re.compile(r"\bshes\b", flags=re.IGNORECASE), "she is")]
templates += [(re.compile(r"\bhes\b", flags=re.IGNORECASE), "he is")]
templates += [(re.compile(r"\bthats\b", flags=re.IGNORECASE), "that is")]
templates += [(re.compile(r"\bwhats\b", flags=re.IGNORECASE), "what is")]
templates += [(re.compile(r"\bwheres\b", flags=re.IGNORECASE), "where is")]
templates += [(re.compile(r"\bhows\b", flags=re.IGNORECASE), "how is")]
templates += [(re.compile(r"\bwhos\b", flags=re.IGNORECASE), "who is")]
templates += [(re.compile(r"\bwhys\b", flags=re.IGNORECASE), "why is")]

templates += [(re.compile(r"\bbtw\b", flags=re.IGNORECASE), "by the way")]
templates += [(re.compile(r"\bcu\b", flags=re.IGNORECASE), "see you")]
templates += [(re.compile(r"\bidk\b", flags=re.IGNORECASE), "i don't know")]
templates += [(re.compile(r"\bimo\b", flags=re.IGNORECASE), "in my opinion")]
templates += [(re.compile(r"\bomg\b", flags=re.IGNORECASE), "oh my god")]
templates += [(re.compile(r"\bthx\b", flags=re.IGNORECASE), "thank you")]
templates += [(re.compile(r"\bthnx\b", flags=re.IGNORECASE), "thank you")]
templates += [(re.compile(r"\bthanks\b", flags=re.IGNORECASE), "thank you")]
templates += [(re.compile(r"\bwtf\b", flags=re.IGNORECASE), "what the fuck")]
templates += [(re.compile(r"\bnp\b", flags=re.IGNORECASE), "no problem")]
templates += [(re.compile(r"\bnvm\b", flags=re.IGNORECASE), "never mind")]
templates += [(re.compile(r"\bdnt\b", flags=re.IGNORECASE), "don't")]
templates += [(re.compile(r"\bgud\b", flags=re.IGNORECASE), "good")]
templates += [(re.compile(r"\bgotcha\b", flags=re.IGNORECASE), "got you")]
templates += [(re.compile(r"\bh8\b", flags=re.IGNORECASE), "hate")]
templates += [(re.compile(r"\bhav\b", flags=re.IGNORECASE), "have")]
templates += [(re.compile(r"\bhru\b", flags=re.IGNORECASE), "how are you")]
templates += [(re.compile(r"\bidc\b", flags=re.IGNORECASE), "i don't care")]
templates += [(re.compile(r"\bk\b", flags=re.IGNORECASE), "okay")]
templates += [(re.compile(r"\bpls\b", flags=re.IGNORECASE), "please")]
templates += [(re.compile(r"\bplz\b", flags=re.IGNORECASE), "please")]
templates += [(re.compile(r"\bzup\b", flags=re.IGNORECASE), "what's up")]
templates += [(re.compile(r"\bwazup\b", flags=re.IGNORECASE), "what's up")]
templates += [(re.compile(r"\bwazzup\b", flags=re.IGNORECASE), "what's up")]
templates += [(re.compile(r"\bwhatsup\b", flags=re.IGNORECASE), "what's up")]
templates += [(re.compile(r"\bwanna\b", flags=re.IGNORECASE), "want to")]
templates += [(re.compile(r"\bgonna\b", flags=re.IGNORECASE), "going to")]

templates += [(re.compile(r"\s+"), " ")]


def preprocess(text):
    for templ, new_str in templates:
        text = re.sub(templ, new_str, text)
    return text.strip()


@app.route("/response", methods=['POST'])
def respond():
    st_time = time.time()

    sentences = request.json["sentences"]

    corrected_sentences = [preprocess(text) for text in sentences]
    corrected_sentences = SPELL_CHECK_MODEL(corrected_sentences)

    total_time = time.time() - st_time
    logger.info(f'Spelling Preprocessing exec time: {total_time:.3f}s')
    return jsonify(corrected_sentences)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
