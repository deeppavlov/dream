import logging
import os
import time

from flask import Flask, request, jsonify
import sentry_sdk

from sentry_sdk.integrations.flask import FlaskIntegration
from deeppavlov import build_model
from common.utils import combined_classes

task_names = [
    "cobot_topics",
    "cobot_dialogact_topics",
    "cobot_dialogact_intents",
    "emotion_classification",
    "sentiment_classification",
    "toxic_classification",
    "factoid_classification",
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
            res = model(sentences, sentences_with_history)
        else:
            raise Exception(
                f"Empty list of sentences or sentences with history received."
                f"Sentences: {sentences} "
                f"Sentences with history: {sentences_with_history}"
            )

        for name, value in zip(task_names, res):
            for i in range(len(value)):
                is_toxic = "toxic" in name and value[i][-1] < 0.5
                if is_toxic:  # sum of probs of all toxic classes >0.5
                    value[i][-1] = 0
                    value[i] = [k / sum(value[i]) for k in value[i]]
                for class_, prob in zip(combined_classes[name], value[i]):
                    if prob == max(value[i]):
                        if class_ != "not_toxic" and name == "toxic_classification":
                            prob = 1
                        ans[i][name] = {class_: float(prob)}
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)

    total_time = time.time() - st_time
    logger.info(f"7in1 exec time: {total_time:.3f}s")
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
    sentences = request.json.get("sentences", [" "])
    sentences_with_hist = request.json.get("sentences_with_history", sentences)
    answer = get_result(sentences, sentences_with_hist)

    logger.info(f"7in1 result: {answer}")
    return jsonify(answer)


@app.route("/batch_model", methods=["POST"])
def batch_respond():
    utterances_with_histories = request.json.get("utterances_with_histories", [[" "]])
    sentences_with_hist = [" [SEP] ".join(s) for s in utterances_with_histories]
    sentences = [s[-1] for s in utterances_with_histories]
    answer = get_result(sentences, sentences_with_hist)

    logger.info(f"7in1 batch result: {answer}")
    return jsonify([{"batch": answer}])


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
