BOOK_SKILL_CHECK_PHRASE = "the last book"
BOOK_SKILL_CHECK_PHRASE2 = 'your favourite book'
BOOK_SKILL_CHECK_PHRASE3 = 'book did impress you the most'
SWITCH_BOOK_SKILL_PHRASE = f"What is {BOOK_SKILL_CHECK_PHRASE} you've read?"
BOOK_SKILL_CHECK_PHRASES = [BOOK_SKILL_CHECK_PHRASE, BOOK_SKILL_CHECK_PHRASE2, BOOK_SKILL_CHECK_PHRASE3]


def skill_trigger_phrases():
    return [SWITCH_BOOK_SKILL_PHRASE]


def book_skill_was_proposed(prev_bot_utt):
    return any([j in prev_bot_utt.get('text', '').lower() for j in BOOK_SKILL_CHECK_PHRASES])
