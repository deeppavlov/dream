#!/usr/bin/env python

import logging
import re
from time import time
import numpy as np

from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk

from zdialog import Request
from src.skill import AlexaPrizeSkill

from common.constants import CAN_CONTINUE_SCENARIO
from common.news import is_breaking_news_requested
from common.utils import get_topics


sentry_sdk.init(getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

with open("./src/google-10000-english-no-swears.txt", "r") as f:
    UNIGRAMS = f.read().splitlines()[:1003]


@app.route("/respond", methods=['POST'])
def respond():
    st_time = time()
    dialogs = request.json['dialogs']
    responses = []
    confidences = []
    attributes = []

    for i, dialog in enumerate(dialogs):
        attr = {}
        response = ""
        confidence = 0.0

        try:
            curr_uttr = dialog["utterances"][-1]
            logger.info(f"User uttr: {curr_uttr['text']}")
            cobot_topics = set(get_topics(dialog['utterances'][-1], which='cobot_topics'))
            cobot_dialogact_topics = set(get_topics(dialog['utterances'][-1], which='cobot_dialogact_topics'))
            news_cobot_dialogacts = {"Science_and_Technology", "Sports", "Politics"}
            news_cobot_topics = {"News"}
            about_news = (news_cobot_dialogacts & cobot_dialogact_topics) | (news_cobot_topics & cobot_topics)

            prev_bot_uttr = {}
            if len(dialog["utterances"]) > 1:
                prev_bot_uttr = dialog["utterances"][-2]
                about_news = about_news or is_breaking_news_requested(prev_bot_uttr, dialog["utterances"][-1])

            entities = []
            for ent in curr_uttr["annotations"].get("ner", []):
                if not ent:
                    continue
                ent = ent[0]
                if not (ent["text"].lower() == "alexa" and curr_uttr["text"].lower()[:5] == "alexa"):
                    if ent["text"].lower() == "trump":
                        entities.append("donald trump")
                    elif ent["text"].lower() == "putin":
                        entities.append("vladimir putin")
                    else:
                        entities.append(ent["text"].lower())

            for ent in curr_uttr["annotations"].get("cobot_nounphrases", []):
                if ent.lower() not in UNIGRAMS:
                    if ent in entities + ["I", 'i']:
                        pass
                    else:
                        if ent.lower() == "trump":
                            entities.append("donald trump")
                        elif ent.lower() == "putin":
                            entities.append("vladimir putin")
                        else:
                            entities.append(ent.lower())

            logger.info(f"Found entities: {entities}")

            if curr_uttr["annotations"].get("intent_catcher", {}).get("yes", {}).get("detected", 0) == 1:
                sent_text = "yes"
            else:
                sent_text = curr_uttr['text'].lower()

            if about_news or ("news" in curr_uttr["text"]) or ("new" in curr_uttr["text"]) or sent_text == "yes":
                news_info, mode, response = eval(AlexaPrizeSkill.handle(Request(user_id=dialog["id"],
                                                                                message=sent_text,
                                                                                raw=entities)).message)
                response = re.sub(r"\n", " ", response)
                if "Unfortunately, I couldn't find anything relevant." in response:
                    confidence = 0.6
                elif ("Sorry, something went wrong." in response) or (
                        "Sign up for the Today’s WorldView newsletter." in response):
                    response = ""
                    confidence = 0.0
                elif mode == "body":
                    confidence = 1.0
                    news_body = [f"The following news is from Washington Post: '{response}'."]
                    response = np.random.choice(news_body)
                    attr["mode"] = "body"
                elif mode == "entity" or mode == "headline":
                    confidence = 0.98
                    attr["can_continue"] = CAN_CONTINUE_SCENARIO
                    attr["mode"] = mode
                    offer_news = [f"I've heard the following news from Washington Post: '{response}'. "
                                  f"Do you want to hear more?",
                                  f"I've read the following news from Washington Post: '{response}'. "
                                  f"Do you want to hear more?",
                                  f"Here is the news from Washington Post: '{response}'. "
                                  f"Do you want to hear more?"]
                    response = np.random.choice(offer_news)
                elif mode == "subtopic" or mode == "topic":
                    confidence = 0.0
                    attr["mode"] = "subtopic"
                    response = ""
                else:
                    # mode is "none"
                    attr["can_continue"] = CAN_CONTINUE_SCENARIO
                    attr["mode"] = None
                    confidence = 0.95
                    offer_news = [f"I could not find some specific news. So, here is one of the latest news "
                                  f"from Washington Post: '{response}'. Do you want to hear more?"]
                    response = np.random.choice(offer_news)
            else:
                response = ""
                confidence = 0.
        except Exception as e:
            logger.exception(f"exception in news_skill {e}")
            with sentry_sdk.push_scope() as scope:
                dialog_replies = []
                for reply in dialog["utterances"]:
                    dialog_replies.append(reply["text"])
                # This will be changed only for the error caught inside and automatically discarded afterward
                scope.set_extra('dialogs', dialog_replies)
                sentry_sdk.capture_exception(e)

        logger.info(f"Response: {response}")
        responses.append(response)
        confidences.append(confidence)
        attributes.append(attr)

    total_time = time() - st_time
    logger.info(f'news_skill exec time: {total_time:.3f}s')
    return jsonify(list(zip(responses, confidences, attributes)))


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
