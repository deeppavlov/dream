import re
from common.utils import get_topics, TOPIC_GROUPS


SUPER_CONFIDENCE = 1.0
HIGH_CONFIDENCE = 0.98
DEFAULT_CONFIDENCE = 0.95
BIT_LOWER_CONFIDENCE = 0.90
ZERO_CONFIDENCE = 0.0

ART_PATTERN = re.compile(r"\b(art|artist|drawing|painting|painter|gallery)(\.|\?|\b)", re.IGNORECASE)


def check_about_art(user_uttr):
    found_topics = get_topics(user_uttr, probs=False, which="all")
    if any([art_topic in found_topics for art_topic in TOPIC_GROUPS["art"]]):
        return True
    elif re.findall(ART_PATTERN, user_uttr["text"]):
        return True
    else:
        return False
