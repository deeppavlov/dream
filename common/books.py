BOOK_SKILL_CHECK_PHRASE = "the recent book"
SWITCH_BOOK_SKILL_PHRASE = f"What is {BOOK_SKILL_CHECK_PHRASE} you've read?"


def skill_trigger_phrases():
    return [SWITCH_BOOK_SKILL_PHRASE]


def book_skill_was_proposed(prev_bot_utt):
    return BOOK_SKILL_CHECK_PHRASE in prev_bot_utt.get('text', '').lower()
