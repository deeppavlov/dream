MOVIE_SKILL_CHECK_PHRASE = "the recent movie"
SWITCH_MOVIE_SKILL_PHRASE = f"What is {MOVIE_SKILL_CHECK_PHRASE} you've watched?"


def movie_skill_was_proposed(prev_bot_utt):
    return MOVIE_SKILL_CHECK_PHRASE in prev_bot_utt.get('text', '').lower()
