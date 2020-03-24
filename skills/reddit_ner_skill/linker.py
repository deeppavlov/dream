#!/usr/bin/env python

import json
import requests
import random
import sentry_sdk
from json import JSONDecodeError
from itertools import chain


class Linker:
    def __init__(self,
                 entity_database,
                 posts_database,
                 phrases,
                 entity_resolution_url,
                 api_key,
                 status_constants,
                 logger,
                 expired_days=8):
        self.logger = logger
        self.entity_database = entity_database
        self.posts_database = posts_database
        self.phrases = phrases
        self.entity_resolution_url = entity_resolution_url
        self.api_key = api_key
        self.status_constants = status_constants
        self.expired_days = expired_days  # Filter news by days
        self.prev_entities = []  # Keep track of entities
        self.prev_posts = []    # and posts
        self.classConstraintsTypes = {  # Constrains to types (nikola tesla != telsa company)
            'PER': [{
                "dataType": "aio:Entity",
                "value": "aio:HumanBeing"
            }],
            'ORG': [{
                "dataType": "aio:Entity",
                "value": "aio:Organisation"
            }],
            'LOC': [{
                "dataType": "aio:Entity",
                "value": "aio:GeographicalArea"
            }],
            'MISC': []
        }

    def _reinit(self):
        """
        Reinitialize in case of new dialog turn
        """
        self.prev_entities = []
        self.prev_posts = []

    def _add(self, entity, post):
        """
        Add entity and post to the list of previously seen
        """
        self.prev_entities.append(entity)
        self.prev_posts.append(post)

    def _get_reaction(self, reaction):
        """
        Get a user reaction (positive/negative/neutral)
        positive - (positive sentiment)/(yes intent)
        negative - (negative sentiment)/(no intent)
        """
        sentiment = reaction['sentiment']
        intent = reaction['intent']
        if sentiment == 'positive' or sentiment == 'negative':
            return sentiment
        elif intent == 'yes' or intent == 'no':
            return intent
        else:
            return 'neutral'

    def _react_to_user(self, user_reaction):
        """
        Get a bot reaction phrase to user phrase
        """
        return random.choice(self.phrases['reaction_phrases'][user_reaction])

    def _status(self, user_reaction, entity, continuation):
        """
        Calculate status (can/must/cannot/etc.)
        """
        if user_reaction == 'negative' or user_reaction == 'no' and continuation:
            return self.status_constants['cannot']
        candidates = self._get_related_entities(entity)
        next_entity, _, _ = self._choose_entity_and_post(candidates)
        if next_entity is None:
            return self.status_constants['cannot']
        else:
            return self.status_constants['can']

    def _get_start_phrase(self, post):
        """
        Get starting phrase based on entity and post
        """
        subreddit = self.posts_database[post]['subreddit']
        return random.choice(self.phrases['subreddit_phrases'][subreddit]['start_phrase'])

    def _get_content_phrase(self, post):
        """
        Get content-related phrase based on post for middle-conversation
        """
        subreddit = self.posts_database[post]['subreddit']
        return random.choice(self.phrases['subreddit_phrases'][subreddit]['content_phrase'])

    def _get_engaging_phrase(self, post):
        """
        Get engaging phrase based on post for the end of phrase
        """
        subreddit = self.posts_database[post]['subreddit']
        return random.choice(self.phrases['subreddit_phrases'][subreddit]['engaging_phrase'])

    def _get_linking_phrase(self, link_type):
        """
        Get connection phrase between two entities
        """
        return random.choice(self.phrases['linking_phrases'][link_type])

    def _get_related_entities(self, entity):
        """
        Get related entities and type of connections from database
        """
        return self.entity_database[entity]['related']

    def _resolve_entity(self, entity):
        """
        Resolve entity by using the key
        """
        headers = {'Content-Type': 'application/json;charset=utf-8', 'x-api-key': self.api_key}
        mention = {'text': entity['text']}
        # Change class constrains in case of poor resolution perfomance
        classConstraints = self.classConstraintsTypes.get(entity['type'], [])
        try:
            resp = requests.request(
                url=self.entity_resolution_url,
                headers=headers,
                data=json.dumps({'mention': mention, 'classConstraints': classConstraints}),
                method='POST',
                timeout=1)
        except (requests.ConnectTimeout, requests.ReadTimeout) as e:
            sentry_sdk.capture_exception(e)
            self.logger.exception("Entity Linker service Timeout")
            resp = requests.Response()
            resp.status_code = 504
        if not resp.ok:
            self.logger.error(f"Request error: status_code={resp.status_code} while resolving entity.")
            return None
        try:
            result = resp.json()['resolvedEntities']
        except JSONDecodeError:
            self.logger.error("JSONDecodeError while resolving entity.")
            return None
        if len(result) > 0:
            return result[0]['value']
        else:
            return None

    def _get_entity_from_user(self, entity_candidates):
        """
        Get entity mentioned by user, resolve it and return its name from the database
        or return None if it haven't been resolved or present in the database.
        """
        entity = None
        for candidate in entity_candidates:
            resolved = self._resolve_entity(candidate)
            if resolved is not None and resolved in self.entity_database:
                entity = resolved
        return entity

    def _get_post(self, entity=None):
        """
        Get entity-related post
        """
        if entity is None:
            return None
        else:
            posts = list(self.entity_database[entity]['posts'])
            return random.choice(posts)

    def _choose_entity_and_post(self, candidates):
        """
        Choose entity, connection type and post from list of candidate entities
        """
        posts = [[(entity, conn, post) for post in self.entity_database[entity]['posts'] if post not in self.prev_posts]
                 for entity, conn in candidates]
        posts = list(chain(posts))
        if len(posts) == 0:
            return None, None, None
        entity, connection, post = random.choice(posts)
        return entity, connection, post

    def _print_phrase(self, phrase, prev_entity, entity, post):
        """
        Print phrase - substitute {...} to names of entities or post data or etc.
        """
        if prev_entity is None:
            prev_entity_label = ""
        else:
            prev_entity_label = self.entity_database[prev_entity]['prefLabel']
        post = self.posts_database[post]
        entity_label = self.entity_database[entity]['prefLabel']
        phrase = phrase.replace('{prev_entity}', prev_entity_label)
        phrase = phrase.replace('{entity}', entity_label)
        phrase = phrase.replace('{post}', post['title'])
        return phrase

    def construct_phrase(self, reaction, entity_candidates, continuation):
        """
        Main method for bot phrase construction
        """
        phrase = ""
        user_reaction = self._get_reaction(reaction)
        self.logger.info(f"user_reaction: {user_reaction}")
        if not continuation or len(self.prev_entities) == 0:  # Start of the dialog
            self.logger.info("Dialog start")
            self._reinit()
            prev_entity = None
            entity = self._get_entity_from_user(entity_candidates)
            post = self._get_post(entity)
            if post is None:
                self.logger.info("No entities were found in KG or database, or not resolved.")
                phrase = ""
                status = self.status_constants['cannot']
                return phrase, status
            phrase += self._get_start_phrase(post) + " "
            phrase += self._get_engaging_phrase(post)
        else:
            self.logger.info("Dialog continuation")
            phrase += self._react_to_user(user_reaction)  # React to user phrase
            prev_entity = self.prev_entities[-1]
            candidates = self._get_related_entities(prev_entity)  # Get all related entities
            entity, link, post = self._choose_entity_and_post(candidates)  # Choose entity and post and connection
            if entity is None:
                self.logger.error("Conversation continuation -> No related entity found (???)")
                phrase = ""
                status = self.status_constants['cannot']
                return phrase, status
            phrase += self._get_connection_phrase(link) + " "  # Connect to next entity
            phrase += self._get_content_phrase(post) + " "
            phrase += self._get_engaging_phrase(post) + " "
        self.logger.info(f"Entity:{entity}")
        self.logger.info(f"Post:{post}")
        self._add(entity, post)
        status = self._status(user_reaction, entity, continuation)
        phrase = self._print_phrase(phrase, prev_entity, entity, post)
        return phrase, status
