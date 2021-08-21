#!/usr/bin/env python

import logging
import time
from random import choice
from collections import defaultdict

from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk

from common.constants import CAN_CONTINUE_SCENARIO
from common.universal_templates import if_chat_about_particular_topic
from common.utils import get_skill_outputs_from_dialog, get_outputs_with_response_from_dialog, get_not_used_template
from common.utils import get_sentiment
from common.greeting import GREETING_QUESTIONS, dont_tell_you_answer


sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

DIALOG_BEGINNING_START_CONFIDENCE = 0.98
DIALOG_BEGINNING_CONTINUE_CONFIDENCE = 0.85
DIALOG_BEGINNING_SHORT_ANSWER_CONFIDENCE = 0.9
MIDDLE_DIALOG_START_CONFIDENCE = 0.7

GREETING_STEPS = list(GREETING_QUESTIONS.keys())
COMMENTS = {
    "neutral": ["Ok. ", "Oh. ", "Huh. ", "Well. ", "Gotcha. ", "Hmm. ", "Aha. "],
    "positive": ["Sounds cool! ", "Great! ", "Wonderful! "],
    "negative": ["Huh... ", "Sounds sad... ", "Sorry... "],
}


def get_next_step(user_utterance, next_step_id, last_comments=None):
    last_comments = [] if last_comments is None else last_comments
    response, confidence, attr = "", 0.0, {}
    if next_step_id < len(GREETING_STEPS):
        sentiment = get_sentiment(user_utterance, probs=False)[0]
        comment = get_not_used_template(used_templates=last_comments, all_templates=COMMENTS[sentiment])
        response = comment + choice(GREETING_QUESTIONS[GREETING_STEPS[next_step_id]])
        if next_step_id == 0:
            confidence = DIALOG_BEGINNING_START_CONFIDENCE
        elif dont_tell_you_answer(user_utterance):
            logger.info(f"More confident as user's answer is too simple: `{user_utterance['text']}`.")
            confidence = DIALOG_BEGINNING_SHORT_ANSWER_CONFIDENCE
        else:
            confidence = DIALOG_BEGINNING_CONTINUE_CONFIDENCE

        attr = {
            "can_continue": CAN_CONTINUE_SCENARIO,
            "greeting_step": GREETING_STEPS[next_step_id],
            "greeting_comment": comment,
        }
    return response, confidence, attr


@app.route("/greeting_skill", methods=["POST"])
def respond():
    st_time = time.time()
    dialogs_batch = request.json["dialogs"]
    confidences = []
    responses = []
    human_attributes = []
    bot_attributes = []
    attributes = []

    for dialog in dialogs_batch:
        bot_attr = {}
        human_attr = dialog["human"]["attributes"]
        human_attr["used_links"] = human_attr.get("used_links", defaultdict(list))
        attr = {}
        response = ""
        confidence = 0.0

        user_utterance = dialog["human_utterances"][-1]
        lets_chat_about_particular_topic = if_chat_about_particular_topic(user_utterance)

        # skill gets full dialog, so we can take into account length_of_the dialog
        if (
            len(dialog["utterances"]) <= 20
            and "?" not in user_utterance["text"]
            and not lets_chat_about_particular_topic
        ):
            logger.info(f"Dialog beginning.")
            prev_skill_outputs = get_skill_outputs_from_dialog(
                dialog["utterances"], skill_name="greeting_skill", activated=True
            )
            prev_response_outputs = [
                get_outputs_with_response_from_dialog(dialog["utterances"], response=response, activated=True)
                for response in GREETING_QUESTIONS[GREETING_STEPS[0]]
            ]
            prev_response_outputs = [
                list_of_outputs for list_of_outputs in prev_response_outputs if len(list_of_outputs) > 0
            ]
            # 2d list to 1d list of dictionaries with hypotheses
            prev_response_outputs = sum(prev_response_outputs, [])

            if len(prev_skill_outputs) > 0:
                greeting_step = prev_skill_outputs[-1]["greeting_step"]
                logger.info(f"Found previous greeting step: `{greeting_step}`.")
                last_comments = [output.get("greeting_comment", "") for output in prev_skill_outputs][-2:]
                next_step_id = GREETING_STEPS.index(greeting_step) + 1
                if next_step_id < len(GREETING_STEPS):
                    response, confidence, attr = get_next_step(user_utterance, next_step_id, last_comments)
            elif len(prev_response_outputs) > 0:
                logger.info(f"Other skills previously asked question from 1st greeting step. Start.")
                response, confidence, attr = get_next_step(user_utterance, next_step_id=1, last_comments=[])
            elif len(dialog["utterances"]) >= 3:
                logger.info(f"No previous greeting steps.")
                response, confidence, attr = get_next_step(user_utterance, next_step_id=0, last_comments=[])
        # TODO: turn on in the middle of the dialog

        if len(response) == 0:
            confidence = 0.0

        responses.append(response)
        confidences.append(confidence)
        human_attributes.append(human_attr)
        bot_attributes.append(bot_attr)
        attributes.append(attr)

    total_time = time.time() - st_time
    logger.info(f"greeting_skill exec time: {total_time:.3f}s")
    return jsonify(list(zip(responses, confidences, human_attributes, bot_attributes, attributes)))


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
