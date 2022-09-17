import logging
import os
import time

from flask import Flask, request, jsonify
import sentry_sdk

from sentry_sdk.integrations.flask import FlaskIntegration
from deeppavlov import build_model
from common.utils import combined_classes

task_names = [
    "emotion_classification",
    "sentiment_classification",
    "toxic_classification",
    "factoid_classification",
    "midas_classification",
    "topics_classification",
]  # ORDER MATTERS!

logger = logging.getLogger(__name__)
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

app = Flask(__name__)


def get_result(sentences, sentences_with_history):
    st_time = time.time()
    ans = [{} for _ in sentences]

    if not sentences:
        logger.exception("Input sentences not received")
        sentences = [" "]
    if not sentences_with_history:
        logger.exception("Input sentences with history not received")
        sentences_with_history = sentences

    try:
        if sentences and sentences_with_history:
            prob_lists = model(sentences, sentences_with_history)
        else:
            raise Exception(
                f"Empty list of sentences or sentences with history received."
                f"Sentences: {sentences} "
                f"Sentences with history: {sentences_with_history}"
            )
        for task_name, prob_list in zip(task_names, prob_lists):
            for i in range(len(prob_list)):
                is_toxic = "toxic" in task_name and prob_list[i][-1] < 0.5
                if is_toxic:  # sum of probs of all toxic classes >0.5
                    prob_list[i][-1] = 0
                    prob_list[i] = [k / sum(prob_list[i]) for k in prob_list[i]]
                ans[i][task_name] = {
                    class_: float(prob) for class_, prob in zip(combined_classes[task_name], prob_list[i])
                }
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)

    total_time = time.time() - st_time
    logger.info(f"Combined classifier exec time: {total_time:.3f}s")
    logger.info(ans)
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
    logger.info(str((sentences, sentences_with_hist)))
    answer = get_result(sentences, sentences_with_hist)

    logger.info(f"6in1 result: {answer}")
    logger.info(f"Combined classifier exec time: {time.time() - t}")
    return jsonify(answer)


@app.route("/batch_model", methods=["POST"])
def batch_respond():
    logger.info("Batch respond")
    t = time.time()
    sep = " [SEP] "
    utterances_with_histories = request.json.get("utterances_with_histories", [[" "]])
    logger.info(utterances_with_histories)
    sentences_with_hist = [sep.join(s) for s in utterances_with_histories]
    sentences = [s[-1].split(sep)[-1] for s in utterances_with_histories]
    logger.info(str((sentences, sentences_with_hist)))
    answer = get_result(sentences, sentences_with_hist)

    logger.info(f"6in1 batch result: {answer}")
    logger.info(f"Combined classifier exec time: {time.time() - t}")
    return jsonify([{"batch": answer}])


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
