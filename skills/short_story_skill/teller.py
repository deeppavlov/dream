#!/usr/bin/env python

import random
import re


class Teller:
    def __init__(self, stories, phrases, status_constants, logger):
        """
        The one that tells tales...
        """
        self.history = []
        self.phrases = phrases
        self.stories = stories
        self.status_constants = status_constants
        self.logger = logger

    def get_story(self, sentence):
        """
        Determine what type of story user requested
        """
        sentence = sentence.lower()
        if re.search("fun((ny)|(niest)){0,1}", sentence):
            return "funny"
        elif re.search("(horror)|(scary)|(frightening)|(spooky)", sentence):
            return "scary"
        elif re.search("(bedtime)|(good)|(kind)|(baby)|(children)|(good night)|(for kid(s){0,1})", sentence):
            return "bedtime"
        else:
            return None

    def choose_story(self, attributes, story_type):
        """
        Choose a story.
        """
        already_told_stories = attributes.get('already_told_stories', [])
        try:  # Try to get a story that haven't been told already
            story = random.choice(
                list(set(self.stories[story_type].keys()) - set(already_told_stories)))
        except IndexError:  # We run out of stories
            phrase = "Oh, I am sorry, but I've run out of stories. Maybe you have any to share with me?"
            status = self.status_constants['cannot']
        else:  # Tell a story setup
            already_told_stories += [story]
            phrase = self.stories[story_type][story]["setup"] + \
                "..." + random.choice(self.phrases['what_happend_next'])
            status = self.status_constants["must"]
            attributes['state'] = 'setup'
            attributes['story'] = story
            attributes['already_told_stories'] = already_told_stories
        return phrase, status, attributes

    def tell_punchline(self, story_name):
        for story_type in self.stories:
            for story in self.stories[story_type]:
                if story == story_name:
                    return self.stories[story_type][story_name]['punchline']
        return 'Oh, sorry, i lost the track of what I was talking about.'

    def tell(self, human_sentence, intents, state):
        """
        Basic logic of story teller
        """
        phrase = ""
        status = self.status_constants["can"]
        confidence = 0.999
        # Set attributes
        attributes = {}
        # Get intent values
        tell_me_a_story = bool(intents.get(
            "tell_me_a_story", {}).get("detected", False))
        yes = bool(intents.get("yes", {}).get("detected", False))
        no = bool(intents.get("no", {}).get("detected", False))
        # Logging
        self.logger.info(f"Human sentence: {human_sentence}")
        self.logger.info(f"tell_me_a_story: {tell_me_a_story}")
        self.logger.info(f"yes: {yes}")
        self.logger.info(f"no: {no}")
        self.logger.info(f"state: {state}")

        # Skill logic
        # We detected an intent firsthand
        if tell_me_a_story or state.get('state', '') == 'asked_for_a_story':
            story_type = self.get_story(human_sentence)
            # User didn't specify the type of story
            if story_type is None:
                if state.get('state', '') == 'asked_for_a_story':
                    phrase = random.choice(self.phrases["which_story"])
                else:
                    phrase = random.choice(
                        self.phrases["sure"]) + " " + random.choice(self.phrases["which_story"])
                status = self.status_constants["must"]
                attributes['state'] = 'which_story'
            else:  # The type of story is already specified in intial intent
                phrase, status, attributes = self.choose_story(attributes, story_type)
        elif state.get('state', '') == 'do_you_mind' and yes:  # Want a story -> yes
            confidence = 1.0
            phrase = random.choice(self.phrases["which_story"])
            status = self.status_constants["must"]
            attributes['state'] = 'which_story'
        elif state.get('state', '') == 'do_you_mind' and no:  # Want a story -> no
            phrase = random.choice(self.phrases["no"])
            status = self.status_constants["can"]
        elif state.get('state', '') == 'do_you_mind':  # Didn't get the answer
            phrase = random.choice(self.phrases["which_story"])
            status = self.status_constants["can"]
            attributes['state'] = 'which_story'
            confidence = 0.75
        elif state.get('state', '') == 'which_story':  # Already asked about which story
            story_type = self.get_story(human_sentence)
            # If we couldn't determine the type of story (don't have such stories)
            if story_type is None:
                phrase = random.choice(self.phrases['no_stories'])
                status = self.status_constants['can']
            else:  # Start telling the story
                phrase, status, attributes = self.choose_story(attributes, story_type)
        elif state.get('state', '') == 'setup' and yes:  # User is still intrigued -> continue
            story_name = state.get('story', '')
            phrase = self.tell_punchline(story_name)
            status = self.status_constants['can']
        elif state.get('state', '') == 'setup' and no:  # User is not interested
            phrase = random.choice(self.phrases['no'])
            status = self.status_constants['cannot']
        elif state.get('state', '') == 'setup':  # Don't know if user is still interested
            story_name = state.get('story', '')
            phrase = self.tell_punchline(story_name)
            status = self.status_constants['can']
            confidence = 0.8
        else:  # Start of a dialog
            phrase = random.choice(self.phrases['start_phrases'])
            status = self.status_constants["must"]
            confidence = 0.5
            attributes['state'] = 'do_you_mind'
        return phrase, confidence, {}, {'short_story_skill_attributes': attributes}, {'can_continue': status}
