import re

from common.utils import get_topics

BOOK_SKILL_CHECK_PHRASE = "the last book"
BOOK_SKILL_CHECK_PHRASE2 = 'your favourite book'
BOOK_SKILL_CHECK_PHRASE3 = 'book did impress you the most'
SWITCH_BOOK_SKILL_PHRASE = f"What is {BOOK_SKILL_CHECK_PHRASE} you've read?"
ASK_TO_REPEAT_BOOK = 'Could you repeat please what book are we discussing?'

QUESTIONS_ABOUT_BOOKS = ["What is your favorite book?",
                         "Which book impressed you the most?",
                         "What is the longest book you have ever read?",
                         "What's a book you like to recommend to other people?",
                         "What is a book that was recommended to you?"]

BOOK_SKILL_CHECK_PHRASES = [BOOK_SKILL_CHECK_PHRASE, BOOK_SKILL_CHECK_PHRASE2,
                            BOOK_SKILL_CHECK_PHRASE3, ASK_TO_REPEAT_BOOK] + QUESTIONS_ABOUT_BOOKS


def skill_trigger_phrases():
    return [SWITCH_BOOK_SKILL_PHRASE] + QUESTIONS_ABOUT_BOOKS


def book_skill_was_proposed(prev_bot_utt):
    return any([j in prev_bot_utt.get('text', '').lower() for j in BOOK_SKILL_CHECK_PHRASES])


BOOK_PATTERN = re.compile(r"(\bbook\b|\bbooks\b|\bread\b|\bwriter\b|bestseller|reading|literature|"
                          r"\bnovel\b|\bnovels\b|\bpoem\b|\bpoems\b)", re.IGNORECASE)


def about_book(annotated_utterance):
    y1 = "Entertainment_Books" in get_topics(annotated_utterance, which="cobot_dialogact_topics")
    y2 = re.search(BOOK_PATTERN, annotated_utterance["text"])
    return y1 or y2
