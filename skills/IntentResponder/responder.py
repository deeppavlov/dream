#!/usr/bin/env python

import json

from respond_funcs import get_respond_funcs

INTENT_RESPONSES_PATH = "./data/intent_response_phrases.json"


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
        self.seen_intents = set()  # Whether the intent have already been detected

    def respond(self, dialog: dict):
        response = ""
        confidence = 0.0

        utt = dialog["utterances"][-1]
        for intent_name, intent_data in utt["annotations"].get("intent_catcher", {}).items():
            print("intent name: " + intent_name, flush=True)
            if intent_data["detected"] and intent_data["confidence"] > confidence:
                if intent_name in self.response_funcs:
                    dialog["seen"] = dialog["called_intents"][intent_name]
                    response = self.response_funcs[intent_name](dialog, self.intent_responses[intent_name])
                    # Special formatter which used in AWS Lambda to identify what was the intent
                    while "#+#" in response:
                        response = response[: response.rfind(" #+#")]
                    self.logger.info(f"Response: {response}; intent_name: {intent_name}")
                    try:
                        response += " #+#{}".format(intent_name)
                    except TypeError:
                        self.logger.error(f"TypeError intent_name: {intent_name} response: {response};")
                        response = "Hmmm... #+#{}".format(intent_name)
                    confidence = intent_data["confidence"]
                    self.seen_intents.add(intent_name)
                    # todo: we need to know what intent was called
                    # current workaround is to use only one intent if several were detected
                    # and to append special token with intent_name
                else:
                    # skip
                    # self.logger.error(f'responder for intent_name: {intent_name} not found')
                    continue
        if response == "":
            self.logger.error(f"response is empty for intents: {utt['annotations'].get('intent_catcher', {}).items()}")
        return response, confidence

    def load_responses(self, intent_responses_filename: str):
        with open(intent_responses_filename, "r") as fp:
            return json.load(fp)
