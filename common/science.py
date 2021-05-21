import re
import json
import pathlib
from common.utils import join_sentences_in_or_pattern


OPINION_REQUESTS_ABOUT_SCIENCE = [
    "Do you like science?",
    "Do you think science is cool?",
    "Many people say they adore science. Do you agree?",
    "Do you think science is a great thing?",
]

OFFER_TALK_ABOUT_SCIENCE = [
    "Would you like to chat about science?",
    "Would you like to talk about science?",
    "I'd like to talk about science, would you?",
]

science_topics = json.load((pathlib.Path(__file__).parent / "science_topics.json").open())

SCIENCE_COBOT_DIALOGACTS = {
    "Science_and_Technology",
    "Entertainment_Books",
}
SCIENCE_COBOT_TOPICS = {
    "Literature",
    "Math",
    "SciTech",
}
SCIENCE_GENERAL_KEY_PHRASES = {
    "science",
    "technology",
    "innovation",
    "breakthroughs",
    "sci tech",
    "scitech",
    "sci-tech",
    "research",
    "scientific",
    "scientist",
    "innovation",
}
SCIENCE_TOPIC_KEY_PHRASES = set(sum([subtopic["key_phrases"] for subtopic in science_topics.values()], []))
SCIENCE_KEY_PHRASES = set((*SCIENCE_GENERAL_KEY_PHRASES, *SCIENCE_TOPIC_KEY_PHRASES))

SCIENCE_TOPIC_KEY_PHRASE_RE = re.compile(
    "(" + "|".join([key_phrase for key_phrase in SCIENCE_TOPIC_KEY_PHRASES]) + ")", re.IGNORECASE
)

for subtopic in science_topics:
    science_topics[subtopic]["key_phrases_re"] = re.compile(
        "(" + "|".join(science_topics[subtopic]["key_phrases"]) + ")", re.IGNORECASE
    )

TRIGGER_PHRASES = OPINION_REQUESTS_ABOUT_SCIENCE + OFFER_TALK_ABOUT_SCIENCE

SCIENCE_COMPILED_PATTERN = re.compile(join_sentences_in_or_pattern(list(SCIENCE_KEY_PHRASES)), re.IGNORECASE)


def skill_trigger_phrases():
    return TRIGGER_PHRASES


def science_skill_was_proposed(prev_bot_utt):
    return any([phrase.lower() in prev_bot_utt.get("text", "").lower() for phrase in TRIGGER_PHRASES])


# %%
import pathlib

pathlib.Path(__file__).parent
# %%
