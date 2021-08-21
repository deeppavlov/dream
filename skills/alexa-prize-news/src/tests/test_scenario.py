from ast import literal_eval

import unittest

from zdialog import Request

from src.content import (
    HELLO_TEXT,
    POSSIBLE_REPLICAS,
    CHOOSE_SUBTOPIC,
    NOTHING_FOUND,
)
from src.skill import AlexaPrizeSkill


class ScenarioTest(unittest.TestCase):
    def setUp(self) -> None:
        self.replicas = [s.split("\n")[0] for s in POSSIBLE_REPLICAS]
        AlexaPrizeSkill.context_storage.__init__(AlexaPrizeSkill)

    def tearDown(self) -> None:
        AlexaPrizeSkill.loader.stop()
        AlexaPrizeSkill.context_storage.clean()

    @staticmethod
    def handle(message, raw=None):
        response = AlexaPrizeSkill.handle(Request(user_id="test", message=message, raw=raw))
        news, mode, message = literal_eval(response.message)
        return mode, message

    def check_mode(self, query, mode):
        m, _ = self.handle(query)
        self.assertEqual(mode, m, query)

    def check_mode_and_random_replica(self, query, mode):
        m, prefix = self.handle(query)
        self.assertEqual(mode, m, query)
        self.assertIn(prefix.split("\n")[0], self.replicas)

    def check_mode_and_replica(self, query, mode, replica):
        m, prefix = self.handle(query)
        self.assertEqual(mode, m, query)
        self.assertIn(replica.split("\n")[0], prefix)

    def check_ner(self, query, mode, entities):
        m, prefix = self.handle(query, entities)
        self.assertEqual(mode, m, query)

    def test_news(self):
        self.check_mode_and_replica("/start", "none", HELLO_TEXT)

        self.check_mode("New York City", "headline")

        self.check_mode("NBA, Rockets face backlash over general manager’s tweet", "headline")

    def test_subtopics(self):
        topic = "outlook"
        self.check_mode_and_replica(topic, "subtopic", CHOOSE_SUBTOPIC(topic, ""))

        self.check_mode("1", "subtopic")

        topic = "lifestyle"
        self.check_mode_and_replica(topic, "subtopic", CHOOSE_SUBTOPIC(topic, ""))

        self.check_mode("second", "subtopic")

        self.check_mode_and_replica(topic, "subtopic", CHOOSE_SUBTOPIC(topic, ""))

        self.check_mode("any", "subtopic")

    def test_ner(self):
        self.check_ner("", "entity", ["Russia"])
        self.check_ner("", "entity", ["Virgin Islands"])
        self.check_ner("", "entity", ["Donald Trump"])
        self.check_ner("", "entity", ["Albert Einstein"])
        self.check_ner("", "entity", ["Clean India"])
        self.check_ner("", "entity", ["Trinity Christian School"])

    def test_not_found(self):
        self.check_mode_and_replica("", "none", NOTHING_FOUND)
        self.check_mode_and_replica("Aidar", "none", NOTHING_FOUND)
        self.check_mode_and_replica("asdabvcfvbfghjfg", "none", NOTHING_FOUND)

    def test_body(self):
        query = "New York City"
        self.check_mode(query, "headline")
        self.check_mode("yes", "body")
        self.check_mode(query, "headline")
        self.check_mode_and_replica("no", "none", HELLO_TEXT)
