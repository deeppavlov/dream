import random
from typing import List

HELLO_TEXT = "What do you want to read about?"

ON_INVALID_COMMAND = "Sorry, I didn't understand you.\n"
ON_ERROR = "Sorry, something went wrong.\n"


POSSIBLE_REPLICAS = [
    "Look what I found!\n\n",
    "This news may interest you!\n\n",
    "Here is something interesting for you!\n\n",
    "Here is the latest news for you!\n\n",
]


def get_random_replica():
    return random.choice(POSSIBLE_REPLICAS)


HEADLINE_PREFIX = lambda query: ""
TOPIC_PREFIX = lambda topic: ""
ENTITY_PREFIX = lambda: ""
SUBTOPIC_PREFIX = lambda subtopic_id, topic: ""

WANT_MORE_TEXT = ""  # "\n\nWant to read more?"

CHOOSE_SUBTOPIC = (
    lambda topic, subtopics_list: f"Among the latest news in {topic}, "
    f"I can identify several areas:\n\n{subtopics_list}"
    f"Which one would you like to know about?"
)

WRONG_SUBTOPIC = (
    ON_INVALID_COMMAND
    + "Choose a subtopic by its number, key phrases, \
    or say 'any' to hear the latest news of the whole topic."
)

NOTHING_FOUND = ""  # "Unfortunately, I couldn't find anything relevant.\nHere is the latest news:\n\n"


def format_headlines(news: List[dict]) -> str:
    headlines = [t["headline"] for t in news if "headline" in t]
    text = "\n\n".join(headlines)
    if text:
        text += WANT_MORE_TEXT
    return text


def format_body(news: dict):
    return news["body"]


def format_subtopics_summaries(summaries) -> str:
    result = ""
    for i, (_, summary) in enumerate(summaries):
        result += f"{i + 1}. {summary}\n\n"
    return result
