from common.utils import is_yes


BREAKING_NEWS_CHECK_WORD = 'Breaking news'
BREAKING_NEWS = f'Oh! {BREAKING_NEWS_CHECK_WORD}! Would you like to hear it?'


def is_breaking_news_requested(prev_bot_utt, user_utt):
    if BREAKING_NEWS_CHECK_WORD.lower() in prev_bot_utt.get('text', '').lower():
        if is_yes(user_utt):
            return True
    return False
