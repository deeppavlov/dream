import logging
import os
import time

from flask import Flask, request, jsonify
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from deeppavlov import build_model

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

try:
    kgdg = build_model("kg_dial_generator.json", download=True)
    test_res = kgdg(["What is the capital of Russia?"], [["Q159"]])
    logger.info("model loaded, test query processed")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = Flask(__name__)


@app.route("/model", methods=["POST"])
def respond():
    tm_st = time.time()
    sentences = request.json["sentences"]
    entities = request.json["entities"]
    if sentences:
        out_uttr = ["" for _ in sentences]
        out_conf = [0.0 for _ in sentences]
    else:
        out_uttr = [""]
        out_conf = [0.0]
    f_sentences = []
    f_entities = []
    nf_numbers = []
    for n, (sentence, entities_list) in enumerate(zip(sentences, entities)):
        if len(sentence.split()) == 1 and not entities_list:
            nf_numbers.append(n)
        else:
            f_sentences.append(sentence)
            f_entities.append(entities_list)

    try:
        generated_utterances, confidences = kgdg(f_sentences, f_entities)
        out_uttr = []
        out_conf = []
        cnt_fnd = 0
        for i in range(len(sentences)):
            if i in nf_numbers:
                out_uttr.append("")
                out_conf.append(0.0)
            else:
                out_uttr.append(generated_utterances[cnt_fnd])
                out_conf.append(confidences[cnt_fnd])
                cnt_fnd += 1

    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
    logger.info(f"wikidata_dial_service exec time: {time.time() - tm_st}")

    return jsonify([out_uttr, out_conf])


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
