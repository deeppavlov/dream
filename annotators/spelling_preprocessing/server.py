import logging
import re
import time
from os import getenv

from deeppavlov import build_model
from flask import Flask, request, jsonify
import sentry_sdk

sentry_sdk.init(getenv('SENTRY_DSN'))


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

SPELL_CHECK_MODEL = build_model(config="brillmoore_wikitypos_en")

templates = []
templates += [(re.compile(r"won't"), "will not")]
templates += [(re.compile(r"\bcant\b"), "can't")]
templates += [(re.compile(r"\bim\b"), "i'm")]
templates += [(re.compile(r"\bu\b"), "you")]
templates += [(re.compile(r"\br\b"), "are")]
templates += [(re.compile(r"\bya\b"), "you")]
templates += [(re.compile(r"\bem\b"), "them")]
templates += [(re.compile(r"\bda\b"), "the")]
templates += [(re.compile(r"\bain't\b"), "is not")]
templates += [(re.compile(r"\bi'd\b"), "i would")]
templates += [(re.compile(r"\bur\b"), "your")]
templates += [(re.compile(r"\bru\b"), "are you")]
templates += [(re.compile(r"\burs\b"), "yours")]

templates += [(re.compile(r"\byall\b"), "you all")]
templates += [(re.compile(r"\by'all\b"), "you all")]
templates += [(re.compile(r"\bshes\b"), "she is")]
templates += [(re.compile(r"\bhes\b"), "he is")]
templates += [(re.compile(r"\bthats\b"), "that is")]
templates += [(re.compile(r"\bwhats\b"), "what is")]
templates += [(re.compile(r"\bwheres\b"), "where is")]
templates += [(re.compile(r"\bhows\b"), "how is")]
templates += [(re.compile(r"\bwhos\b"), "who is")]
templates += [(re.compile(r"\bwhys\b"), "why is")]

templates += [(re.compile(r"\bbtw\b"), "by the way")]
templates += [(re.compile(r"\bcu\b"), "see you")]
templates += [(re.compile(r"\bidk\b"), "i don't know")]
templates += [(re.compile(r"\bimo\b"), "in my opinion")]
templates += [(re.compile(r"\bomg\b"), "oh my god")]
templates += [(re.compile(r"\bthx\b"), "thank you")]
templates += [(re.compile(r"\bthnx\b"), "thank you")]
templates += [(re.compile(r"\bthanks\b"), "thank you")]
templates += [(re.compile(r"\bwtf\b"), "what the fuck")]
templates += [(re.compile(r"\bnp\b"), "no problem")]
templates += [(re.compile(r"\bnvm\b"), "never mind")]
templates += [(re.compile(r"\bdnt\b"), "don't")]
templates += [(re.compile(r"\bgud\b"), "good")]
templates += [(re.compile(r"\bgotcha\b"), "got you")]
templates += [(re.compile(r"\bh8\b"), "hate")]
templates += [(re.compile(r"\bhav\b"), "have")]
templates += [(re.compile(r"\bhru\b"), "how are you")]
templates += [(re.compile(r"\bidc\b"), "i don't care")]
templates += [(re.compile(r"\bk\b"), "okay")]
templates += [(re.compile(r"\bpls\b"), "please")]
templates += [(re.compile(r"\bplz\b"), "please")]
templates += [(re.compile(r"\bzup\b"), "what's up")]
templates += [(re.compile(r"\bwazzup\b"), "what's up")]
templates += [(re.compile(r"\bwhatsup\b"), "what's up")]
templates += [(re.compile(r"\bwanna\b"), "want to")]
templates += [(re.compile(r"\bgonna\b"), "going to")]

templates += [(re.compile(r"\s+"), " ")]


def preprocess(text):
    for templ, new_str in templates:
        text = re.sub(templ, new_str, re.IGNORECASE)
    return text.strip()


@app.route("/response", methods=['POST'])
def respond():
    st_time = time.time()

    sentences = request.json["sentences"]

    corrected_sentences = SPELL_CHECK_MODEL(sentences)

    corrected_sentences = [preprocess(text) for text in corrected_sentences]

    total_time = time.time() - st_time
    logger.info(f'Spelling Preprocessing exec time: {total_time:.3f}s')
    return jsonify(corrected_sentences)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
