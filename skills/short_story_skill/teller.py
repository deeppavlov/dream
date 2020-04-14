#!/usr/bin/env python

import random
import re
from itertools import chain


class Teller:
    def __init__(self, stories, phrases, status_constants, logger):
        """
        The one that tells tales...
        """
        self.history = []
        self.phrases = phrases
        self.stories = stories
        self.setups_punchlines = {story['setup']: story['punchline'] for story in chain.from_iterable(stories.values())}
        self.status_constants = status_constants
        self.logger = logger

    def which_story(self, sentence):
        """
        Determine what type of story user requested
        """
        if re.search("fun((ny)|(niest)){0,1}", sentence):
            return "funny"
        elif re.search("(horror)|(scary)|(frightening)|(spooky)", sentence):
            return "scary"
        elif re.search("(bedtime)|(good)|(kind)|(baby)|(children)|(good night)|(for kid(s){0,1})", sentence):
            return "bedtime"
        else:
            return None

    def search_phrases(self, search_phrases, phrase):
        return any([re.search(search_phrase, phrase) for search_phrase in search_phrases])

    def tell(self, human_sentence, bot_sentence, intents):
        """
        Basic logic of story teller
        """
        phrase = ""
        status = self.status_constants["can"]
        confidence = 0.999
        setup = [setup for setup in self.setups_punchlines if re.search(setup, bot_sentence)]
        if len(setup) == 1:  # Getting the story the bot was telling
            setup = setup[0]
        elif len(setup) == 0:
            setup = None
        else:
            self.logger.error(f"Multiple setups matching: {setup}")
        # Get intent values
        tell_me_a_story = bool(intents.get("tell_me_a_story", {}).get("detected", False))
        yes = bool(intents.get("yes", {}).get("detected", False))
        no = bool(intents.get("no", {}).get("detected", False))
        # Logging
        self.logger.info(f"Human sentence: {human_sentence}")
        self.logger.info(f"Bot sentence: {bot_sentence}")
        self.logger.info(f"tell_me_a_story: {tell_me_a_story}")
        self.logger.info(f"yes: {yes}")
        self.logger.info(f"no: {no}")
        self.logger.info(f"setup: {setup}")

        # Skill logic
        if self.search_phrases(self.phrases['start_phrases'], bot_sentence) and yes:  # Want a story -> yes
            phrase = random.choice(self.phrases["which_story"])
            status = self.status_constants["must"]
        elif self.search_phrases(self.phrases['start_phrases'], bot_sentence) and no:  # Want a story -> no
            phrase = random.choice(self.phrases["no"])
            status = self.status_constants["cannot"]
        elif self.search_phrases(self.phrases['start_phrases'], bot_sentence):  # Already started a dialog + yes
            phrase = random.choice(self.phrases["which_story"])
            status = self.status_constants["can"]
            confidence = 0.8
        elif self.search_phrases(self.phrases["which_story"], bot_sentence):  # Already asked about which story
            story_type = self.which_story(human_sentence)
            if story_type is None:  # If we couldn't determine the type of story (don't have such stories)
                phrase = random.choice(self.phrases['no_stories'])
                status = self.status_constants['can']
            else:
                story = random.choice(self.stories[story_type])  # Tell story setup
                phrase = story["setup"] + "..." + random.choice(self.phrases['what_happend_next'])
                status = self.status_constants['must']
        elif setup and yes:  # User is still intrigued -> continue
            phrase = self.setups_punchlines[setup]
            status = self.status_constants['can']
        elif setup and no:  # User is not interested
            phrase = random.choice(self.phrases['no'])
            status = self.status_constants['cannot']
        elif setup:  # Don't know if user is still interested
            phrase = self.setups_punchlines[setup]
            status = self.status_constants['can']
            confidence = 0.8
        elif tell_me_a_story:  # We detected an intent firsthand
            story_type = self.which_story(human_sentence)
            if self.which_story(human_sentence) is None:  # User didn't specify the type of story
                phrase = random.choice(self.phrases["sure"]) + " " + random.choice(self.phrases["which_story"])
                status = self.status_constants["must"]
            else:  # The type of story is already specified in intial intent
                phrase = random.choice(self.phrases["sure"]) + " " + random.choice(self.phrases["which_story"])
                story = random.choice(self.stories[story_type])
                phrase = story["setup"] + '... ' + random.choice(self.phrases['what_happend_next'])
                status = self.status_constants["must"]
        else:  # Start of a dialog
            phrase = random.choice(self.phrases['start_phrases'])
            status = self.status_constants["must"]
            confidence = 0.5
        return phrase, confidence, status
