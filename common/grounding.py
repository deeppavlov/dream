import re
import logging

logger = logging.getLogger(__name__)

patterns = [
    "what are we talking about",
    "what do we talk about",
    "what are you talking about",
    "what do you talk about",
    "what it is about",
    "what is it about",
    "what we are discussing",
    "what are we discussing",
    "what do you mean",
    "i lost common ground",
    r"^what[\?\.]?$"
]
re_patterns = re.compile(r"(" + "|".join(patterns) + r")", re.IGNORECASE)


def what_we_talk_about(utterance):
    if isinstance(utterance, dict):
        utterance = utterance["text"]
    return re.search(re_patterns, utterance) is not None
