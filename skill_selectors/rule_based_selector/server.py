#!/usr/bin/env python

import logging
import time
from typing import List

from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk


sentry_sdk.init(getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


class RuleBasedSelector():
    """
    Rule-based skill selector which choosing among TransferTransfo, Base AIML and Alice AIML
    """
    wh_words = {"what", "when", "where", "which", "who", "whom", "whose", "why", "how"}
    first_question_words = {
        "do", "have", "did", "had", "are", "is", "am", "will",
        "would", "should", "shall", "may", "might", "can", "could"
    }

    sensitive_topics = {"Politics", "Celebrities", "Religion", "Sex_Profanity", "Sports",
                        "News", "Psychology"
                        }
    # `General_ChatIntent` sensitive in case when `?` in reply
    sensitive_dialogacts = {"Opinion_RequestIntent", "General_ChatIntent"
                            }

    def __init__(self, **kwargs):
        logger.info("Skill selector Initialized")

    def _is_question(self, tokens):
        return tokens[0] in self.first_question_words or len(set(tokens).intersection(self.wh_words)) > 0

    def __call__(self, states_batch, **kwargs) -> List[List[str]]:

        skill_names = []

        for dialog in states_batch:
            skills_for_uttr = []
            reply = dialog['utterances'][-1]['text'].replace("\'", " \'").lower()
            # tokens = reply.split()
            intents = dialog['utterances'][-1]['annotations']['intent_catcher'].values()
            intent_detected = any([i['detected'] == 1 for i in intents])

            cobot_topics = dialog['utterances'][-1]['annotations']['cobot_topics']['text']
            sensitive_topics_detected = any([t in self.sensitive_topics for t in cobot_topics])
            cobot_dialogacts = dialog['utterances'][-1]['annotations']['cobot_dialogact']['intents']
            sensitive_dialogacts_detected = any([(t in self.sensitive_dialogacts and "?" in reply)
                                                 for t in cobot_dialogacts])

            blist_topics_detected = dialog['utterances'][-1]['annotations']['blacklisted_words']['restricted_topics']

            if "/new_persona" in dialog['utterances'][-1]['text']:
                skills_for_uttr.append("personality_catcher")  # TODO: rm crutch of personality_catcher
            elif intent_detected:
                skills_for_uttr.append("intent_responder")
            elif blist_topics_detected or (sensitive_topics_detected and sensitive_dialogacts_detected):
                skills_for_uttr.append("program_y_dangerous")
                skills_for_uttr.append("cobotqa")
            # elif self._is_question(tokens):
            elif "Information_RequestIntent" in cobot_dialogacts:
                skills_for_uttr.append("cobotqa")
                skills_for_uttr.append("program_y")
                # skills_for_uttr.append("transfertransfo")
                # skills_for_uttr.append("retrieval_chitchat")
            else:
                skills_for_uttr.append("program_y")
                # skills_for_uttr.append("transfertransfo")
                # skills_for_uttr.append("retrieval_chitchat")

            # always add dummy_skill
            skills_for_uttr.append("dummy_skill")
            skill_names.append(skills_for_uttr)

        return skill_names


selector = RuleBasedSelector()


@app.route("/selected_skills", methods=['POST'])
def respond():
    st_time = time.time()
    states_batch = request.json["states_batch"]
    skill_names = selector(states_batch)
    total_time = time.time() - st_time
    logger.info(f'rule_based_selector exec time: {total_time:.3f}s')
    return jsonify(skill_names)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
