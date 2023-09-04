import re

ITALY_PATTERN = re.compile(
    r"(italy|italian(s)?|(italian)? city|people|language|rome|venice)(\.|\?)|",
    re.IGNORECASE,
)

ITALY_TRAVEL_SKILL_CHECK_PHRASE = "italy"
ITALY_TRAVEL_SKILL_CHECK_PHRASE2 = "Have you ever been to {ITALY_TRAVEL_SKILL_CHECK_PHRASE}"
ITALY_TRAVEL_SKILL_CHECK_PHRASE3 = "Do you like {ITALY_TRAVEL_SKILL_CHECK_PHRASE}?"
SWITCH_ITALY_TRAVEL_SKILL_PHRASE = f"Let's talk about {ITALY_TRAVEL_SKILL_CHECK_PHRASE}"
ASK_TO_REPEAT_ITALY = "Could you repeat please what place are we discussing?"
WHAT_RECOMMEND_IN_ITALY = "What do you recommend to see in  {ITALY_TRAVEL_SKILL_CHECK_PHRASE}?"
QUESTIONS_ABOUT_ITALY = [
    "What is your favorite place in {ITALY_TRAVEL_SKILL_CHECK_PHRASE}?",
    "What place do you like to visit in {ITALY_TRAVEL_SKILL_CHECK_PHRASE}?",
    WHAT_RECOMMEND_IN_ITALY,
]

ITALY_TRAVEL_SKILL_CHECK_PHRASES = [
    ITALY_TRAVEL_SKILL_CHECK_PHRASE,
    ITALY_TRAVEL_SKILL_CHECK_PHRASE2,
    ITALY_TRAVEL_SKILL_CHECK_PHRASE3,
    ASK_TO_REPEAT_ITALY,
] + QUESTIONS_ABOUT_ITALY


def italy_travel_skill_was_proposed(prev_bot_utt):
    return any([j in prev_bot_utt.get("text", "").lower() for j in ITALY_TRAVEL_SKILL_CHECK_PHRASES])
