#!/usr/bin/env python

import logging
import time
import numpy as np

from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk

from common.utils import is_yes, is_no


sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
misheard_responses = np.array(
    [
        (
            "Sorry, I misheard you. Sometimes it’s difficult for me to understand speech well. "
            "Sorry. It's just my usual dimness."
        ),
        "Sorry, I didn't catch that. Could you say it again, please?",
        "I couldn't hear you. I beg your pardon?",
        "I beg your pardon?",
        (
            "Sorry, I didn't catch that. Only it's like a fruit machine in there. "
            "I open my mouth, and I never know "
            "if it’s going to come out three oranges or two lemons and a banana."
        ),
    ]
)


@app.route("/misheard_respond", methods=["POST"])
def misheard_response():
    st_time = time.time()
    dialogs_batch = request.json["dialogs"]
    final_confidences = []
    final_responses = []
    final_human_attributes = []
    final_bot_attributes = []

    for dialog in dialogs_batch:
        prev_user_utt = None
        if len(dialog["human_utterances"]) > 1:
            prev_user_utt = dialog["human_utterances"][-2]
        bot_attributes = dialog["bot"]["attributes"]
        human_attributes = dialog["human"]["attributes"]
        current_user_utt = dialog["human_utterances"][-1]
        prev_bot_utt = dialog["bot_utterances"][-1] if len(dialog["bot_utterances"]) > 0 else {}
        logger.debug(
            f"MISHEARD ASR INPUT: current utt text: {current_user_utt['text']};"
            f"bot attrs: {bot_attributes}; user attrs: {human_attributes}"
            f"HYPOTS: {current_user_utt['hypotheses']}"
            f"PREV BOT UTT: {prev_bot_utt}"
        )
        if bot_attributes.get("asr_misheard") is True and prev_bot_utt["active_skill"] == "misheard_asr":
            bot_attributes["asr_misheard"] = False
            if is_yes(current_user_utt):
                hypots = prev_user_utt["hypotheses"]
                logger.debug(f"PREV HYPOTS: {hypots}")
                candidates = []
                confs = []
                for resp in hypots:
                    if resp["skill_name"] != "misheard_asr":
                        candidates.append(resp["text"])
                        confs.append(resp["confidence"])
                final_responses.append(candidates)
                final_confidences.append(confs)
                final_human_attributes.append([human_attributes] * len(candidates))
                final_bot_attributes.append([bot_attributes] * len(candidates))
            elif is_no(current_user_utt):
                response = "What is it that you'd like to chat about?"
                final_responses.append([response])
                final_confidences.append([1.0])
                final_human_attributes.append([human_attributes])
                final_bot_attributes.append([bot_attributes])
            else:
                final_responses.append(["sorry"])
                final_confidences.append([0.0])
                final_human_attributes.append([human_attributes])
                final_bot_attributes.append([bot_attributes])
        else:
            bot_attributes["asr_misheard"] = False
            if current_user_utt["annotations"]["asr"]["asr_confidence"] == "very_low":
                final_responses.append([np.random.choice(misheard_responses)])
                final_confidences.append([1.0])
                final_human_attributes.append([human_attributes])
                final_bot_attributes.append([bot_attributes])
            elif current_user_utt["annotations"]["asr"]["asr_confidence"] == "medium":
                response = f"Excuse me, I misheard you. Have you said: \"{dialog['human_utterances'][-1]['text']}\"?"
                final_responses.append([response])
                final_confidences.append([1.0])
                bot_attributes["asr_misheard"] = True
                final_human_attributes.append([human_attributes])
                final_bot_attributes.append([bot_attributes])
            else:
                final_responses.append(["sorry"])
                final_confidences.append([0.0])
                final_human_attributes.append([human_attributes])
                final_bot_attributes.append([bot_attributes])

    total_time = time.time() - st_time
    logger.info(f"misheard_asr#misheard_respond exec time: {total_time:.3f}s")
    resp = list(zip(final_responses, final_confidences, final_human_attributes, final_bot_attributes))
    logger.debug(f"misheard_asr#misheard_respond OUTPUT: {resp}")
    return jsonify(resp)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
