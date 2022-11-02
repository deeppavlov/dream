import logging
import os
import time

from flask import Flask, request, jsonify
import sentry_sdk

from sentry_sdk.integrations.flask import FlaskIntegration
from deeppavlov import build_model
from common.utils import combined_classes

logger = logging.getLogger(__name__)
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

app = Flask(__name__)


def get_result(sentences, sentences_with_history, postannotations=False):
    logger.debug((sentences, sentences_with_history, postannotations))
    ans = [{} for _ in sentences]
    if not sentences:
        logger.exception("Input sentences not received")
        sentences = [" "]
    if not sentences_with_history:
        logger.exception("Input sentences with history not received")
        sentences_with_history = sentences
    if not postannotations:
        data = [
            sentences,  # emo was trained without history
            sentences,  # sentiment was trained without history
            sentences,  # toxic was trained without history
            sentences,  # factoid was trained without history
            sentences_with_history,  # midas was trained with history
            sentences,  # deeppavlov topics was trained without history
            sentences,  # cobot topics was trained without history
            sentences,  # cobot dialogact topics is now trained without history
            sentences,  # cobot dialogact intents is now trained without history
        ]
    elif postannotations:
        # While using postannotations, we annotate only for toxic class
        data = [[] for _ in range(9)]
        data[2] = sentences
    try:
        prob_lists = model(*data)
        for task_name, prob_list in zip(combined_classes, prob_lists):
            # we assume toxic has 7 classes
            for i in range(len(prob_list)):
                if prob_list[i]:
                    ans[i][task_name] = {
                        class_: round(float(prob), 2) for class_, prob in zip(combined_classes[task_name], prob_list[i])
                    }
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)

    return ans


try:
    model = build_model("combined_classifier.json", download=False)
    logger.info("Making test res")
    test_res = get_result(["a"], ["a"])
    logger.info("model loaded, test query processed")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e


@app.route("/model", methods=["POST"])
def respond():
    t = time.time()
    logger.info("Respond")
    sentences = request.json.get("sentences", [" "])
    sentences_with_hist = request.json.get("sentences_with_history", sentences)
    answer = get_result(sentences, sentences_with_hist, postannotations=False)
    logger.exception(f"9in1 result: {answer}")
    logger.info(f"Combined classifier exec time: {time.time() - t}")
    return jsonify(answer)


@app.route("/batch_model", methods=["POST"])
def batch_respond():
    t = time.time()
    sep = " [SEP] "
    utterances_with_histories = request.json.get("utterances_with_histories", [[" "]])
    sentences_with_hist = [sep.join(s) for s in utterances_with_histories]
    sentences = [s[-1].split(sep)[-1] for s in utterances_with_histories]
    answer = get_result(sentences, sentences_with_hist, postannotations=True)
    logger.debug(f"9in1 batch result: {answer}")
    logger.info(f"Combined classifier exec time: {time.time() - t}")
    return jsonify([{"batch": answer}])


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
