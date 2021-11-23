import logging
import re
import time
from os import getenv

import en_core_web_sm
import sentry_sdk
from flask import Flask, request, jsonify

#  import spacy - not worked
#  nlp = spacy.load("en_core_web_sm") - not worked
nlp = en_core_web_sm.load()

sentry_sdk.init(getenv("SENTRY_DSN"))


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

logger.info("I am ready to respond")

np_ignore_list = {
    "'s",
    "i",
    "me",
    "my",
    "myself",
    "we",
    "our",
    "ours",
    "ourselves",
    "you",
    "you're",
    "you've",
    "you'll",
    "you'd",
    "your",
    "yours",
    "yourself",
    "yourselves",
    "he",
    "him",
    "his",
    "himself",
    "she",
    "she's",
    "her",
    "hers",
    "herself",
    "it",
    "it's",
    "its",
    "itself",
    "they",
    "them",
    "their",
    "theirs",
    "themselves",
    "what",
    "which",
    "who",
    "whom",
    "this",
    "that",
    "that'll",
    "these",
    "those",
    "am",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "having",
    "do",
    "does",
    "did",
    "doing",
    "a",
    "an",
    "the",
    "and",
    "but",
    "if",
    "or",
    "because",
    "as",
    "until",
    "while",
    "of",
    "at",
    "by",
    "for",
    "with",
    "about",
    "against",
    "between",
    "into",
    "through",
    "during",
    "before",
    "after",
    "above",
    "below",
    "to",
    "from",
    "up",
    "down",
    "in",
    "out",
    "on",
    "off",
    "over",
    "under",
    "again",
    "further",
    "then",
    "once",
    "here",
    "there",
    "when",
    "where",
    "why",
    "how",
    "all",
    "any",
    "both",
    "each",
    "few",
    "more",
    "most",
    "other",
    "some",
    "such",
    "no",
    "nor",
    "not",
    "only",
    "own",
    "same",
    "so",
    "than",
    "too",
    "very",
    "s",
    "t",
    "can",
    "will",
    "just",
    "don",
    "don't",
    "should",
    "should've",
    "now",
    "d",
    "ll",
    "m",
    "o",
    "re",
    "ve",
    "y",
    "ain",
    "aren",
    "aren't",
    "couldn",
    "couldn't",
    "didn",
    "didn't",
    "doesn",
    "doesn't",
    "hadn",
    "hadn't",
    "hasn",
    "hasn't",
    "haven",
    "haven't",
    "isn",
    "isn't",
    "ma",
    "mightn",
    "mightn't",
    "mustn",
    "mustn't",
    "needn",
    "needn't",
    "shan",
    "shan't",
    "shouldn",
    "shouldn't",
    "wasn",
    "wasn't",
    "weren",
    "weren't",
    "won",
    "won't",
    "wouldn",
    "wouldn't",
    "my name",
    "your name",
    "wow",
    "yeah",
    "yes",
    "ya",
    "cool",
    "okay",
    "more",
    "some more",
    " a lot",
    "a bit",
    "another one",
    "something else",
    "something",
    "anything",
    "someone",
    "anyone",
    "play",
    "mean",
    "a lot",
    "a little",
    "a little bit",
    "sure",
}

words_ignore_in_np = re.compile(r"(which|what)", re.IGNORECASE)


def noun_phrase_extraction(input_text):
    if input_text:
        input_text = input_text.lower()
        doc = nlp(input_text)
        noun_chunks = [str(nounph) for nounph in doc.noun_chunks if str(nounph) not in np_ignore_list]

        # based on dependency parsing these should be the most likely topics
        augmented_noun_chunks = []

        subjects = [
            token for token in doc if any([t in token.dep_ for t in ["obj", "subj", "comp"]]) and not token.is_stop
        ]
        subjects = [str(subject) for subject in subjects]

        augmented_noun_chunks = [nounph for subject in subjects for nounph in noun_chunks if subject in nounph.split()]
        augmented_noun_chunks = list(set(augmented_noun_chunks))

        if not augmented_noun_chunks:
            # if only one word is VBG, add it to the list
            vbg = [token for token in doc if ("VBG" == token.tag_)]
            if len(vbg) == 1:
                noun_chunks.extend([vbg[0].text])
            return noun_chunks

        augmented_noun_chunks = [re.sub(words_ignore_in_np, "", nounph).strip() for nounph in augmented_noun_chunks]

        return augmented_noun_chunks
    return []


symbols_for_nounphrases = re.compile(r"[^0-9a-zA-Z \-]+")
spaces = re.compile(r"\s\s+")


def get_result(request):
    st_time = time.time()
    sentences = request.json["sentences"]
    logger.debug(f"Input sentences: {sentences}")

    nounphrases_batch = [noun_phrase_extraction(sentence) for sentence in sentences]
    nounphrases_batch = [
        [re.sub(symbols_for_nounphrases, "", nounph).strip() for nounph in nounphrases]
        for nounphrases in nounphrases_batch
    ]
    nounphrases_batch = [[re.sub(spaces, " ", nounph) for nounph in nounphrases] for nounphrases in nounphrases_batch]
    result = [[nounph for nounph in nounphrases if len(nounph)] for nounphrases in nounphrases_batch]

    logger.debug(f"spacy_nounphrases output: {result}")
    total_time = time.time() - st_time
    logger.info(f"spacy_nounphrases exec time: {total_time:.3f}s")
    return result


@app.route("/respond", methods=["POST"])
def nounphrases_respond():
    result = get_result(request)
    return jsonify(result)


@app.route("/respond_batch", methods=["POST"])
def nounphrases_respond_batch():
    result = get_result(request)
    return jsonify([{"batch": result}])


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
