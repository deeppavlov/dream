import logging
import os
import time
from flask import Flask, request, jsonify
import sentry_sdk
from deeppavlov import build_model

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
sentry_sdk.init(os.getenv("SENTRY_DSN"))

app = Flask(__name__)

config_name = os.getenv("CONFIG")
top_n = int(os.getenv("TOP_N"))

try:
    fact_retrieval = build_model(config_name, download=True)
    logger.info("model loaded")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e


@app.route("/model", methods=["POST"])
def respond():
    st_time = time.time()
    inp = request.json
    dialog_history_batch = inp.get("dialog_history", [])
    entity_substr_batch = inp.get("entity_substr", [[] for _ in dialog_history_batch])
    entity_tags_batch = inp.get("entity_tags", [[] for _ in dialog_history_batch])
    entity_pages_batch = inp.get("entity_pages", [[] for _ in dialog_history_batch])
    sentences_batch = []
    for dialog_history in dialog_history_batch:
        if (len(dialog_history[-1].split()) > 2 and "?" in dialog_history[-1]) or len(dialog_history) == 1:
            sentence = dialog_history[-1]
        else:
            sentence = " ".join(dialog_history)
        sentences_batch.append(sentence)

    contexts_with_scores_batch = [[] for _ in sentences_batch]
    try:
        contexts_with_scores_batch = []
        contexts_batch, scores_batch, from_linked_page_batch, numbers_batch = fact_retrieval(
            sentences_batch, entity_substr_batch, entity_tags_batch, entity_pages_batch
        )
        for contexts, scores, from_linked_page_list, numbers in zip(
            contexts_batch, scores_batch, from_linked_page_batch, numbers_batch
        ):
            contexts_with_scores_linked, contexts_with_scores_not_linked, contexts_with_scores_first = [], [], []
            for context, score, from_linked_page, number in zip(contexts, scores, from_linked_page_list, numbers):
                if from_linked_page and number > 0:
                    contexts_with_scores_linked.append((context, score, number))
                elif from_linked_page and number == 0:
                    contexts_with_scores_first.append((context, score, number))
                else:
                    contexts_with_scores_not_linked.append((context, score, number))
            contexts_with_scores_linked = sorted(contexts_with_scores_linked, key=lambda x: (x[1], x[2]), reverse=True)
            contexts_with_scores_not_linked = sorted(
                contexts_with_scores_not_linked, key=lambda x: (x[1], x[2]), reverse=True
            )
            contexts_with_scores = []
            contexts_with_scores += [(context, score, True) for context, score, _ in contexts_with_scores_first]
            contexts_with_scores += [
                (context, score, True) for context, score, _ in contexts_with_scores_linked[: top_n // 2]
            ]
            contexts_with_scores += [
                (context, score, False) for context, score, _ in contexts_with_scores_not_linked[: top_n // 2]
            ]
            contexts_with_scores_batch.append(contexts_with_scores)
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
    total_time = time.time() - st_time
    logger.info(f"fact retrieval exec time = {total_time:.3f}s")
    return jsonify(contexts_with_scores_batch)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
