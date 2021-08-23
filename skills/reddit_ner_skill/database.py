#!/usr/bin/env python

import re
import requests
import json
import datetime
from itertools import chain
from collections import Counter


class Client:
    def __init__(self, api_key, entity_resolution_url, knowledge_query_url):
        """
        Class for Evi KG requests
        """
        self.entity_resolution_url = entity_resolution_url
        self.knowledge_query_url = knowledge_query_url
        self.headers = {'Content-Type': 'application/json;charset=utf-8', 'x-api-key': api_key}

    def get_knowledge_query_answer(self, query, variableBindings, timeout_in_millis):
        req = requests.request(
            url=self.knowledge_query_url, headers=self.headers,
            data=json.dumps({'query': query, "variableBindings": variableBindings}),
            method='POST').json()
        return req

    def get_knowledge_entity_resolution(self, mention, classConstraints, timeout_in_millis):
        req = requests.request(
            url=self.entity_resolution_url,
            headers=self.headers,
            data=json.dumps({'mention': mention, 'classConstraints': classConstraints}),
            method='POST').json()
        return req


class EntityDatabase:
    def __init__(self):
        """
        Database class.

        Lets you contain entities and related post, add entity properties and relations between
        entities and find related to given entities.
        """
        self.data = dict()
        self.counter = Counter()

    def __iter__(self):
        for key in self.data:
            yield key

    def __len__(self):
        return len(self.data)

    def __contains__(self, item):
        return item in self.data

    def __getitem__(self, key):
        return self.data[key]

    def __str__(self):
        return self.data.__str__()

    def __setitem__(self, entity, post):
        """
        Add entity and related post
        """
        if entity in self:
            if post not in self.data[entity]['posts']:
                self.data[entity]['posts'].append(post)
            else:
                return None
        else:
            self.data[entity] = {
                'posts': [post],
                'base_class': '',
                'prefLabel': '',
                'related': [],  # [{'entity':entity, 'connection_type':connection}]
                'classes': []
            }
        self.counter[entity] += 1

    def _recount(self):
        self.counter = Counter()
        for entity in self:
            self.counter[entity] = len(self[entity]['posts'])

    def save(self, filename):
        fp = open(filename, 'w')
        json.dump(self.data, fp)

    def load(self, filename):
        self.data = json.load(open(filename))
        assert type(self.data) == dict
        self._recount()
        return self

    def most_common(self, n=None):
        """
        Return most common entities and their number
        """
        return self.counter.most_common(n)

    def get_posts(self, entity, expired_days=3, topic=None):
        """
        Get posts related to entity, optionally filtered by days and topic
        """
        today = datetime.today()
        posts = self.data[entity]['posts']
        filtered = list()
        for post in posts:
            post_day = datetime.fromtimestamp(int(post['created_utc']))  # filter news by timedate and topic:
            if topic is not None and post['topic'] != topic:  # topic
                continue
            if (today - post_day).days > expired_days and post['content_category'] == 'news':  # date
                continue
            filtered.append(post)
        return filtered

    def get_related_entities(self, entity):
        """
        Get the list of related entities
        """
        return self.data[entity]['related']  # [(entity, connection_type)]

    def get_related_posts(self, entity, expired_days=3, topic=None):
        """
        Get all posts from related entities
        """
        related = list(
            chain(
                [
                    {
                        'posts': self.get_posts(related['entity'], expired_days, topic),
                        'connection_type':related['connection_type']
                    }
                    for related in self.get_related_entities(entity)
                ]
            )
        )
        return related

    def add_connection(self, original_entity, related_entity, connection):
        """
        Add a connection from original_entity to related_entity
        """
        if original_entity in self and related_entity in self:
            self.data[original_entity]['related'].append((related_entity, connection['name']))
            if connection['bidirectional']:
                self.data[related_entity]['related'].append((original_entity, connection['name']))

    def add_classes(self, entity, entity_classes, client):
        """
        Add list of classes to entity with respect to entity_classes
        """
        query = {"text": "query cls | m <aio:isAnInstanceOf> cls"}
        variableBindings = [
            {
                "variable": "m",
                "dataType": "aio:Entity",
                "value": entity
            }
        ]
        try:
            #             time.sleep(1)
            answer = client.get_knowledge_query_answer(
                query=query,
                variableBindings=variableBindings,
                timeout_in_millis=10000
            )
            results = {a['bindingList'][0]['value'] for a in answer['results']}
        except Exception as e:
            print(e)
            results = set()
        # add classes to an entity
        for base_class in entity_classes:
            classes = set(entity_classes[base_class])
            classes.add(base_class)
            if base_class in results:
                self.data[entity]['classes'] = self.data[entity]['classes'].union(classes.intersection(results))
                if base_class != 'aio:Thing':  # aio:Thing - common base class for miscellanious types of entities
                    self.data[entity]['base_class'] = base_class
            if self.data[entity]['base_class'] == "":
                self.data[entity]['base_class'] = "aio:Thing"

    def add_class(self, entity, cls, client):
        if cls in self.data[entity]['classes']:
            return True
        query = {"text": "query | a <aio:isAnInstanceOf> cls"}
        variableBindings = [
            {
                "variable": "a",
                "dataType": "aio:Entity",
                "value": entity
            },
            {
                "variable": "cls",
                "dataType": "aio:Entity",
                "value": cls
            }
        ]
        try:
            #             time.sleep(1)
            answer = client.get_knowledge_query_answer(
                query=query,
                variableBindings=variableBindings,
                timeout_in_millis=1000
            )
            result = (answer['status'] == "YES")
        except Exception as e:
            print(e)
            result = False
        if result:
            self.data[entity]['classes'].append(cls)
        return result

    def add_preflabel(self, entity, client):
        """
        Add preferable label (name) to entity
        """
        query = {"text": "query lab | m <aio:prefLabel> lab"}
        variableBindings = [
            {
                "variable": "m",
                "dataType": "aio:Entity",
                "value": entity
            }
        ]
        try:
            #             time.sleep(1)
            answer = client.get_knowledge_query_answer(
                query=query,
                variableBindings=variableBindings,
                timeout_in_millis=10000
            )
            label = answer['results'][0]['bindingList'][0]['value']
        except Exception as e:
            print(e)
            label = re.sub(r"[^A-Za-z ]+", '', entity[4:].replace("_", " "))
        self.data[entity]['prefLabel'] = label
