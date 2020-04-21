from common.utils import is_yes

# this way news skill offers latest news when nothing specific found
OFFER_BREAKING_NEWS = "Would you like to hear the latest news?"
# statuses in attributes for news skill
OFFERED_BREAKING_NEWS_STATUS = "offered_breaking_news"
OFFERED_NEWS_DETAILS_STATUS = "offered_news_details"
OPINION_REQUEST_STATUS = "opinion_request"
NEWS_GIVEN = "offered_news_details"
WHAT_TYPE_OF_NEWS = ["What other kinds of news would you want to discuss?",
                     "What are the other kinds of news you'd love to hear about?",
                     "What else would you want to hear news about?",
                     "What type of news do you prefer?"]

# from emo skill connections to news skill
BREAKING_NEWS_CHECK_WORD = 'Breaking news'
BREAKING_NEWS = f'Oh! {BREAKING_NEWS_CHECK_WORD}! Would you like to hear it?'

NEWS_DUPLICATES = WHAT_TYPE_OF_NEWS


def skill_trigger_phrases():
    return [BREAKING_NEWS]


def is_breaking_news_requested(prev_bot_utt, user_utt):
    if BREAKING_NEWS_CHECK_WORD.lower() in prev_bot_utt.get('text', '').lower():
        if is_yes(user_utt):
            return True
    return False
