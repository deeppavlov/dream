#!/usr/bin/env python

import json

from typing import List
from respond_funcs import get_respond_funcs

INTENT_RESPONSES_PATH = './data/intent_response_phrases.json'


class Responder:
    def __init__(self, logger):
        """

        The responder for each of the detected intents.
        If the are more than one detected intent, we select the one with the maximum confidence.
        The confidence of the response is equal to the confidence of detection.

        """
        self.logger = logger
        self.intent_responses = self.load_responses(INTENT_RESPONSES_PATH)
        self.response_funcs = get_respond_funcs()
        # self.logger.info("Exiter initialized")

    def respond(self, utterances: List):
        responses, confidences = [], []
        for utt in utterances:
            response = ""
            confidence = 0.0
            for intent_name, intent_data in utt['annotation']['intent_catcher'].items():
                if intent_data['detected'] and intent_data['confidence'] > confidence:
                    response = self.response_funcs[intent_name](utt, self.intent_responses[intent_name])
                    # Special formatter which used in AWS Lambda to identify what was the intent
                    response += " #+#{}".format(intent_name)
                    confidence = intent_data['confidence']
            responses.append(response)
            confidences.append(confidence)
        return list(zip(responses, confidences))

    def load_responses(self, intent_responses_filename: str):
        with open(intent_responses_filename, 'r') as fp:
            return json.load(fp)
