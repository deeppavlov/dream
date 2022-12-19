import logging
import os
import time
import json
import re

import sentry_sdk
from flask import Flask, jsonify, request

from deeppavlov import build_model

sentry_sdk.init(os.getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)

config_name = os.getenv("CONFIG")

with open("numbers.json", "r") as f:
    NUMBERS = json.load(f)

templates = []

templates += [(re.compile(r"^alexa ", flags=re.IGNORECASE), "")]
templates += [
    (
        re.compile(
            r"(?<=\b[a-z])\. (?=[a-z]\.)|(?<=\b[a-z]\. [a-z])\.(?! [a-z]\.)",
            flags=re.IGNORECASE,
        ),
        "",
    )
]
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
templates += [(re.compile(r"\bid k\b", flags=re.IGNORECASE), "i don't know")]
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
templates += [(re.compile(r"\bna\b", flags=re.IGNORECASE), "no")]

for written_number, int_number in list(NUMBERS.items())[::-1]:
    templates += [
        (
            re.compile(r"\b" + written_number + r"\b", flags=re.IGNORECASE),
            str(int_number),
        )
    ]


def hundred_repl(match_obj):
    second_term = 0 if match_obj.group(2) is None else int(match_obj.group(2))
    return str(int(match_obj.group(1)) * 100 + second_term)


templates += [(re.compile(r"\b([1-9]) hundred( [0-9]{1,2})?\b"), hundred_repl)]


def ten_power_3n_repl(match_obj):
    number_groups = [1, 6, 10, 13]
    for i_ng, ng in enumerate(number_groups):
        if match_obj.group(ng) is not None:
            start = ng + 1
            n = 4 - i_ng
            break
    result = 0
    for i in range(start, start + n):
        power = (start + n - i - 1) * 3
        result += 0 if match_obj.group(i) is None else int(match_obj.group(i)) * 10 ** power
    return str(result)


templates += [
    (
        re.compile(
            r"(\b(?:([1-9][0-9]{0,2}) billion)(?:( [1-9][0-9]{0,2}) million)?(?:( [1-9][0-9]{0,2}) thousand)?"
            r"( [1-9][0-9]{0,2})?\b)|"
            r"(\b(?:([1-9][0-9]{0,2}) million)(?:( [1-9][0-9]{0,2}) thousand)?( [1-9][0-9]{0,2})?\b)|"
            r"(\b(?:([1-9][0-9]{0,2}) thousand)( [1-9][0-9]{0,2})?\b)|"
            r"(\b([1-9][0-9]{0,2})\b)",
            flags=re.IGNORECASE,
        ),
        ten_power_3n_repl,
    )
]

templates += [
    (
        re.compile(r"(?<![0-9] )\b([0-9]{1,2}) ([0-9]{1,2})\b(?! [0-9])", flags=re.IGNORECASE),
        r"\1\2",
    )
]
templates += [(re.compile(r"\s+"), " ")]


def preprocess(text):
    for templ, new_str in templates:
        text = re.sub(templ, new_str, text)
    return text.strip()


try:
    spelling_preprocessing_model = build_model(config_name, download=True)
    if config_name == "levenshtein_corrector_ru.json":
        r = "я ге видел малако"
        logger.info(f"Original: {r}. Corrected: {spelling_preprocessing_model([r])}")
        logger.info("spelling_preprocessing model is loaded.")
    else:
        r = "tge shop is cloed"
        logger.info(f"Original: {r}. Corrected: {spelling_preprocessing_model([r])}")
        logger.info("spelling_preprocessing model is loaded.")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()

    sentences = request.json["sentences"]
    sentences = [text.lower() for text in sentences]
    if config_name == "brillmoore_wikitypos_en.json":
        sentences = [preprocess(text) for text in sentences]

    corrected_sentences = spelling_preprocessing_model(sentences)
    corrected_sentences = [
        text if "/alexa" not in orig_text else orig_text for text, orig_text in zip(corrected_sentences, sentences)
    ]

    logger.info(f"spelling_preprocessing results: {list(zip(sentences, corrected_sentences))}")

    total_time = time.time() - st_time
    logger.info(f"spelling_preprocessing exec time: {total_time:.3f}")
    return jsonify(corrected_sentences)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8074)
