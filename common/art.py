import re


SUPER_CONFIDENCE = 1.0
HIGH_CONFIDENCE = 0.98
DEFAULT_CONFIDENCE = 0.95
BIT_LOWER_CONFIDENCE = 0.90
ZERO_CONFIDENCE = 0.0

ART_PATTERN = re.compile(r"\b(art|artist|drawing|painting|painter|gallery)(\.|\?|\b)", re.IGNORECASE)
