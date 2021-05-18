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
RE_RECORDING_TEMPLATE = r"(((are|do|can|could|will|would|have|had|whether) " \
                        r"(you|amazon|echo)|conversation( is| (can|could) be)?) " \
                        r"(record|snoop|spy|wiretap|(see(ing)?|watch(ing)?|track(ing)?) " \
                        r"me|listen(ing)? (to )?(me|my)))"
RE_RECORDING_TEMPLATE2 = r"((keep)? (protect) (the)? (information)? (protect|secret))"
re_recording_patterns = re.compile(rf"({RE_RECORDING_TEMPLATE}|{RE_RECORDING_TEMPLATE2})",
                                   re.IGNORECASE)


def are_we_recorded(utterance):
    if isinstance(utterance, dict):
        utterance = utterance["text"]
    return re.search(re_recording_patterns, utterance) is not None


def what_we_talk_about(utterance):
    if isinstance(utterance, dict):
        utterance = utterance["text"]
    return re.search(re_grounding_patterns, utterance) is not None
