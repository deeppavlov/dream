import re
import logging

logger = logging.getLogger(__name__)

grounding_patterns = [
    "what are we talking about",
    "what we are talking about",
    "what do we talk about",
    "what are you talking about",
    "what you are talking about",
    "what do you talk about",
    "what it is about",
    "what is it about",
    "what we are discussing",
    "what are we discussing",
    "what do you mean",
    "i lost common ground",
    r"^what[\?\.]?$"
]
re_grounding_patterns = re.compile(r"(" + "|".join(grounding_patterns) + r")", re.IGNORECASE)

re_recording_patterns = re.compile(
    r"(((are|do|can|could|will|would|have|had|whether) (you|amazon|echo)|conversation( is| (can|could) be)?) "
    r"(record|snoop|spy|wiretap|(see(ing)?|watch(ing)?|track(ing)?) me|listen(ing)? (to )?(me|my)))", re.IGNORECASE)


def are_we_recorded(utterance):
    if isinstance(utterance, dict):
        utterance = utterance["text"]
    return re.search(re_recording_patterns, utterance) is not None


def what_we_talk_about(utterance):
    if isinstance(utterance, dict):
        utterance = utterance["text"]
    return re.search(re_grounding_patterns, utterance) is not None
