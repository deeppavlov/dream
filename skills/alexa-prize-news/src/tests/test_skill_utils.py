import unittest

from src.skill import AlexaPrizeSkill
from src.skill.utils import *


class SkillUtilsTest(unittest.TestCase):
    def tearDown(self) -> None:
        AlexaPrizeSkill.loader.stop()

    def test_clean_message(self):
        self.assertEqual("politics", clean_message("give me news about politics"))
        self.assertEqual("politics", clean_message("tell me about politics"))

    def test_parse_entity(self):
        ner_index = {
            "donald trump": [0, 1],
            "russia": [2],
        }
        self.assertEqual("donald trump", parse_entity(ner_index, "give me news about donald trump"))
        self.assertEqual("russia", parse_entity(ner_index, "russia"))
        self.assertEqual(None, parse_entity(ner_index, "none"))

    def test_score_news_by_entities(self):
        ner_index = {
            "donald trump": [0, 1, 2],
            "russia": [1],
            "vladimir putin": [0, 1],
        }
        self.assertEqual([0, 1, 2], score_news_by_entities(ner_index, ["Donald Trump"], 3))
        self.assertEqual([1], score_news_by_entities(ner_index, ["Russia"], 3))
        self.assertEqual([1, 0, 2], score_news_by_entities(ner_index, ["Donald Trump", "Russia", "Vladimir Putin"], 3))
        self.assertEqual([], score_news_by_entities(ner_index, [], 3))

    def test_parse_topic(self):
        topics = ["politics", "sport"]
        self.assertEqual("politics", parse_topic(topics, "politix"))
        self.assertEqual("sport", parse_topic(topics, "sports topic"))
        self.assertEqual(None, parse_topic(topics, "Donal Trump politics"))
        self.assertEqual(None, parse_topic(topics, "none"))

    def test_get_paired(self):
        self.assertEqual([], get_paired([]))
        self.assertEqual([], get_paired(["a"]))
        self.assertEqual(["a b", "b c"], get_paired(["a", "b", "c"]))

    def test_get_match_score(self):
        words = ["first", "second", "third"]

        def test_phrase(expected, phrase):
            self.assertAlmostEqual(expected, get_match_score(phrase.split(), words), msg=phrase, delta=0.05)

        test_phrase(0, "none")
        test_phrase(1, "first")
        test_phrase(0.8, "frst")
        test_phrase(0.8, "frst scond")
        test_phrase(0.5, "first none")
        test_phrase((0.8 + 1 + 0) / 3, "frst third none")


if __name__ == "__main__":
    unittest.main()
