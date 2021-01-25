import logging
import os
from flask import Flask, request, jsonify
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from deeppavlov import build_model

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
sentry_sdk.init(dsn=os.getenv('SENTRY_DSN'), integrations=[FlaskIntegration()])

config_name = os.getenv("CONFIG")
NER_INPUT = True

try:
    kbqa = build_model(config_name, download=True)
    if NER_INPUT:
        test_res = kbqa(["What is the capital of Russia?"],
                        ["What is the capital of Russia?"], ["-1"], [["Russia"]], [[]])
    else:
        test_res = kbqa(["What is the capital of Russia?"])
    logger.info("model loaded, test query processed")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)

app = Flask(__name__)


@app.route("/model", methods=['POST'])
def respond():
    inp = request.json
    questions = inp.get("x_init", [" "])
    template_types = ["-1" for _ in questions]
    entities = inp.get("entities", [[]])
    entity_types = [[] for _ in questions]
    sanitized_questions, sanitized_entities = [], []
    if len(questions) == len(entities):
        for question, entities_list in zip(questions, entities):
            if question.startswith("/") or "/alexa" in question or any(["/" in entity for entity in entities_list]):
                sanitized_questions.append(" ")
                sanitized_entities.append([])
            else:
                sanitized_questions.append(question)
                sanitized_entities.append(entities_list)
    if NER_INPUT:
        kbqa_input = [sanitized_questions, sanitized_questions, template_types, sanitized_entities, entity_types]
    else:
        kbqa_input = [questions]
    res = [("Not Found", 0.0)] * len(questions)
    try:
        res = kbqa(*kbqa_input)
        if res:
            res = [(answer, float(conf)) for answer, conf in res]
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
    return jsonify(res)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
