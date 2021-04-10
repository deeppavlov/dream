import re
import logging

logger = logging.getLogger(__name__)

patterns = [
    "are we talking about",
    "are you talking about",
    "what it is about",
    "what is it about",
    "what we are discussing",
    "what do you mean",
    "i lost common ground",
    "what"
]
re_patterns = re.compile(r"^(" + "|".join(patterns) + r")[\?\.]?$", re.IGNORECASE)


def what_we_talk_about(utterance):
    if isinstance(utterance, dict):
        utterance = utterance["text"]
    return re.search(re_patterns, utterance) is not None
