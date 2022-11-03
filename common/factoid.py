import re

FACTOID_NOTSURE_CONFIDENCE = 0.1
FACTOID_THRESHOLD = 0.5

FACT_REGEXP = re.compile(r"fact about", re.IGNORECASE)
WHAT_REGEXP = re.compile(
    r"((what (is|are) (a |an |the )?{subject}\?)|" r"(what (a |an |the ){subject} (is|are)\?))", re.IGNORECASE
)

DONT_KNOW_ANSWER = [
    "Sorry I can't answer these kinds of questions yet. "
    "My engineers are hard at work teaching me new things every day.",
    "Sorry but I'm not yet able to answer these kinds of questions. My engineers are still teaching me.",
    "My apologies but I can't answer these kinds of questions yet. I'm still learning!",
]
