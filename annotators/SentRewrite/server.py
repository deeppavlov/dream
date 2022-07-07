import logging
import time
from os import getenv

import sentry_sdk
from flask import Flask, jsonify, request
from sentrewrite import recover_mentions

sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route("/sentrewrite", methods=["POST"])
def respond():
    st_time = time.time()
    # utterances_histories: list of dialogs, each dialog is a list of utterances, each utterance is a list of sentences.
    # [dialog -> utterance -> sentence]
    utterances_histories = request.json["utterances_histories"]
    annotation_histories = request.json["annotation_histories"]

    # [dialog_annotations -> annotated_utterance -> sentence -> ner (dict)]
    # {'confidence': 0.9985795021057129, 'end_pos': 5, 'start_pos': 0, 'text': 'Messi', 'type': 'PERSON'}
    ner_histories = []
    for dialog, dialog_annotations in zip(utterances_histories, annotation_histories):
        ner_histories.append([])
        for utterance, annotated_utterance in zip(dialog, dialog_annotations):
            # noinspection PyInterpreter
            n_segments = len(utterance)
            ner_histories[-1].append(annotated_utterance.get("ner", n_segments * [[]]))

    ret = []

    for i, (dialog, ner_dialog) in enumerate(zip(utterances_histories, ner_histories)):
        # keep only 4 latest utterances, w.r.t. two turns
        if len(dialog) > 4:
            dialog = dialog[-4:]
            ner_dialog = ner_dialog[-4:]
        ret.append(recover_mentions(dialog, ner_dialog))

    logger.info(f"output: {ret}")
    total_time = time.time() - st_time
    logger.info(f"sent. rewrite exec time: {total_time: .3f}s")

    return jsonify(ret)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
