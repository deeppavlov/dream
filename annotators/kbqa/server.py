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

config_name = os.getenv("CONFIG")
NER_INPUT = True

try:
    kbqa = build_model(config_name, download=True)
    if NER_INPUT:
        test_res = kbqa(
            ["What is the capital of Russia?"],
            ["What is the capital of Russia?"],
            ["-1"],
            [["Russia"]],
            [[[("country", 1.0)]]],
        )
    else:
        test_res = kbqa(["What is the capital of Russia?"])
    logger.info("model loaded, test query processed")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = Flask(__name__)


@app.route("/model", methods=["POST"])
def respond():
    inp = request.json
    questions = inp.get("x_init", [" "])
    template_types = ["-1" for _ in questions]
    entities = inp.get("entities", [[]])
    entity_tags = inp.get("entity_tags", [[]])
    sanitized_questions, sanitized_entities = [], []
    nf_numbers = []
    if len(questions) == len(entities):
        for n, (question, entities_list) in enumerate(zip(questions, entities)):
            if question.startswith("/") or "/alexa" in question or any(["/" in entity for entity in entities_list]):
                nf_numbers.append(n)
            elif not entities_list:
                nf_numbers.append(n)
            else:
                sanitized_questions.append(question)
                sanitized_entities.append(entities_list)
    kbqa_input = []
    if sanitized_questions:
        if NER_INPUT:
            kbqa_input = [sanitized_questions, sanitized_questions, template_types, sanitized_entities, entity_tags]
        else:
            kbqa_input = [sanitized_questions]
    logger.info(f"kbqa_input: {kbqa_input}")
    default_resp = {"qa_system": "kbqa", "answer": "", "confidence": 0.0}
    out_res = [default_resp for _ in questions]
    try:
        st_time = time.time()
        if kbqa_input:
            res = kbqa(*kbqa_input)
            if res:
                out_res = []
                cnt_fnd = 0
                for i in range(len(questions)):
                    if i in nf_numbers:
                        out_res.append(default_resp)
                    else:
                        if cnt_fnd < len(res):
                            answer, conf = res[cnt_fnd]
                            out_res.append({"qa_system": "kbqa", "answer": answer, "confidence": float(conf)})
                            cnt_fnd += 1
        logger.info(f"kbqa exec time: {time.time() - st_time} out_res {out_res}")
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
    return jsonify(out_res)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
