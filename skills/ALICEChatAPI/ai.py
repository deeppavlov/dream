#!/usr/bin/env python

import aiml
import os
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class Chatbot():
    def __init__(self):
        self._kernel = aiml.Kernel()

    def initialize(self, aiml_dir):
        for name in os.listdir(aiml_dir):
            if name.endswith('.aiml'):
                logger.info(f'loading templates from: {name}')
                self._kernel.learn(os.sep.join([aiml_dir, name]))
        properties_file = open(os.sep.join([aiml_dir, 'bot.properties']))
        for line in properties_file:
            parts = line.split('=')
            key = parts[0]
            value = parts[1]
            self._kernel.setBotPredicate(key, value)

    def respond(self, input, session_id):
        response = self._kernel.respond(input, sessionID=session_id)
        return response

    def reset(self):
        self._kernel.resetBrain()


def main():
    chatbot = Chatbot()
    chatbot.initialize("aiml-dir")  # parameter is the aiml directory

    while True:
        n = input("Input: ")
        print(chatbot.respond(n))


if __name__ == '__main__':
    main()
