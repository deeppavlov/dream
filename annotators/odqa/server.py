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

try:
    odqa = build_model(config_name, download=True)
    test_res = odqa(["What is the capital of Russia?"], ["the capital, russia"], [["the capital", "russia"]], [""])
    logger.info("model loaded, test query processed")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = Flask(__name__)


def check_utterance(question, bot_sentence):
    question = question.lower()
    bot_sentence = bot_sentence.lower()
    check = False
    lets_talk_phrases = ["let's talk about", "let us talk about", "let's discuss", "let us discuss",
                         "what do you think about", "what's your opinion about", "do you know"]
    for phrase in lets_talk_phrases:
        if phrase in question:
            return True
    greeting_phrases = ["what do you wanna talk about",
                        "what do you want to talk about",
                        "what would you like to chat about",
                        "what are we gonna talk about",
                        "what are your hobbies",
                        "what are your interests"]
    for phrase in greeting_phrases:
        if phrase in bot_sentence:
            return True
    return check


@app.route("/model", methods=['POST'])
def respond():
    questions = request.json.get("human_sentences", [" "])
    bot_sentences = request.json.get("bot_sentences", [" "])
    questions = [question.lstrip("alexa") for question in questions]
    nounphr_list = request.json.get("entity_substr", [])
    questions_nounphr = [", ".join(elem) for elem in nounphr_list]
    if not nounphr_list:
        nounphr_list = [[] for _ in questions]
    entities_batch = request.json.get("entities", [])
    if not entities_batch:
        entities_batch = [[] for _ in questions]
    input_entities = []
    for question, bot_sentence, entities_list in zip(questions, bot_sentences, entities_batch):
        if len(entities_list) == 1:
            input_entities.append(entities_list)
        else:
            input_entities.append([])

    res = []
    try:
        res = odqa(questions, questions_nounphr, nounphr_list, input_entities)
        res = [[elem[i] for elem in res] for i in range(len(res[0]))]
        for i in range(len(res)):
            res[i][1] = float(res[i][1])
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
    return jsonify(res)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
