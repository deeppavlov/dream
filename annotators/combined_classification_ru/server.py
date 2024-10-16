import logging
import os
import time

from flask import Flask, request, jsonify
import sentry_sdk

from sentry_sdk.integrations.flask import FlaskIntegration
from deeppavlov import build_model
from common.combined_classes import combined_classes


supported_tasks = [
    "emotion_classification",
    "sentiment_classification",
    "toxic_classification",
    "factoid_classification",
    "midas_classification",
    "topics_ru",
]

combined_classes = {task: combined_classes[task] for task in combined_classes if task in supported_tasks}
combined_classes["toxic_classification"] = ["not_toxic", "toxic"]  # As Russian toxic supports only TWO classes

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

logger = logging.getLogger(__name__)


def get_result(sentences, sentences_with_history, postannotations=False):
    logger.debug((sentences, sentences_with_history, postannotations))
    ans = [{} for _ in sentences]
    if not sentences:
        logger.exception("Input sentences not received")
        sentences = [" "]
    # if not sentences_with_history:
    #    logger.exception("Input sentences with history not received")
    #    sentences_with_history = sentences
    data = [sentences for _ in range(len(combined_classes))]
    try:
        prob_lists = model(*data)
        for task_name, prob_list in zip(combined_classes, prob_lists):
            for i in range(len(prob_list)):
                ans[i][task_name] = {
                    class_: round(float(prob), 2) for class_, prob in zip(combined_classes[task_name], prob_list[i])
                }
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)

    return ans


try:
    model = build_model("combined_classifier_ru.json", download=True)
    logger.info("Making test res")
    test_res = get_result(["a"], ["a"])
    logger.info("model loaded, test query processed")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = Flask(__name__)


@app.route("/model", methods=["POST"])
def respond():
    t = time.time()
    sentences = request.json.get("sentences", [" "])
    sentences_with_hist = request.json.get("sentences_with_history", sentences)
    answer = get_result(sentences, sentences_with_hist)
    logger.debug(f"combined_classification result: {answer}")
    logger.info(f"combined_classification exec time: {time.time() - t}")
    return jsonify(answer)


@app.route("/batch_model", methods=["POST"])
def batch_respond():
    t = time.time()
    sep = " [SEP] "
    utterances_with_histories = request.json.get("utterances_with_histories", [[" "]])
    sentences_with_hist = [sep.join(s) for s in utterances_with_histories]
    sentences = [s[-1].split(sep)[-1] for s in utterances_with_histories]
    answer = get_result(sentences, sentences_with_hist)
    logger.debug(f"combined_classification batch result: {answer}")
    logger.info(f"combined_classification exec time: {time.time() - t}")
    return jsonify([{"batch": answer}])
