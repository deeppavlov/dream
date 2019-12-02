#!/usr/bin/env python

import logging
import time
import re
import numpy as np

from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk


sentry_sdk.init(getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

cool_answers = np.array(["Interesting.",
                         "Cool.",
                         "Okay.",
                         "Nice to meet you."])
repeat_name = "I didn't get your name. Could you, please, repeat it."
repeat_location = "I didn't get your location. Could you, please, repeat it."


@app.route("/respond", methods=['POST'])
def respond():
    st_time = time.time()
    dialogs_batch = request.json["dialogs"]
    confidences = []
    responses = []
    human_attributes = []
    bot_attributes = []

    for dialog in dialogs_batch:
        response = ""
        confidence = 0.
        human_attr = {}
        bot_attr = {}

        curr_user_uttr = dialog["utterances"][-1]["text"].lower()
        curr_user_annot = dialog["utterances"][-1]["annotations"]
        try:
            prev_bot_uttr = dialog["utterances"][-2]["text"].lower()
        except IndexError:
            prev_bot_uttr = ""

        got_name = False
        # is_about_name = "what is your name" in prev_bot_uttr or "what's your name" in prev_bot_uttr
        is_about_name = re.search(r"(what is|what's|whats|tell me) your? name", prev_bot_uttr)

        if is_about_name or prev_bot_uttr == repeat_name:
            logger.info(f"Asked for a name in {prev_bot_uttr}")
            for ent in curr_user_annot.get("ner", []):
                if not ent:
                    continue
                ent = ent[0]
                logger.info(f"Found name `{ent['text']}`")
                human_attr["name"] = " ".join([n.capitalize() for n in ent["text"].split()])
                response = f"Nice to meet you. I will remember your name, {human_attr['name']}."
                confidence = 1.
                got_name = True
            if not got_name:
                response = repeat_name
                confidence = 0.9

        got_location = False
        # is_about_location = "what is your location" in prev_bot_uttr or "what's your location" in prev_bot_uttr
        is_about_location = re.search(r"((what is|what's|whats|tell me) your? location|"
                                      r"where are you from|where do you live|where are you)", prev_bot_uttr)
        if is_about_location or prev_bot_uttr == repeat_location:
            for ent in curr_user_annot.get("ner", []):
                if not ent:
                    continue
                ent = ent[0]
                logger.info(f"Found location `{ent['text']}`")
                human_attr["location"] = " ".join([n.capitalize() for n in ent["text"].split()])
                response = f"Cool! I will remember your location is {human_attr['location']}."
                confidence = 1.
                got_location = True
            if not got_location:
                response = repeat_location
                confidence = 0.9

        tell_my_name = re.search(r"(what is|what's|whats|tell me|you know|you remember|memorize|say) my name",
                                 curr_user_uttr)
        if tell_my_name:
            logger.info(f"Asked to memorize user's name in {curr_user_uttr}")
            if dialog["human"]["profile"]["name"] is None:
                response = f"Sorry, we are still not familiar. What is your name?"
                confidence = 0.98
            else:
                name = dialog["human"]["profile"]["name"]
                response = f"Your name is {name}."
                confidence = 1.

        tell_my_location = re.search(r"((what is|what's|whats|tell me|you know|you remember|memorize|say) my location|"
                                     r"where (am i|i am)(\snow)?)",
                                     curr_user_uttr)
        if tell_my_location:
            logger.info(f"Asked to memorize user's location in {curr_user_uttr}")
            if dialog["human"]["profile"]["location"] is None:
                response = f"Sorry, I don't have this information. But you can tell me. What is your location?"
                confidence = 0.98
            else:
                name = dialog["human"]["profile"]["location"]
                response = f"Your location is {name}."
                confidence = 1.

        responses.append(response)
        confidences.append(confidence)
        human_attributes.append(human_attr)
        bot_attributes.append(bot_attr)

    total_time = time.time() - st_time
    logger.info(f'personal_info_skill exec time: {total_time:.3f}s')
    return jsonify(list(zip(responses, confidences, human_attributes, bot_attributes)))


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
