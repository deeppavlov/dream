from common.utils import is_yes

# this way news skill offers latest news when nothing specific found
OFFER_BREAKING_NEWS = "Would you like to hear the latest news?"
OFFER_TOPIC_SPECIFIC_NEWS = "Would you like to hear news about TOPIC?"
# statuses in attributes for news skill
OFFER_TOPIC_SPECIFIC_NEWS_STATUS = "offered_specific_news"
OFFERED_BREAKING_NEWS_STATUS = "offered_breaking_news"
OFFERED_NEWS_DETAILS_STATUS = "offered_news_details"
OPINION_REQUEST_STATUS = "opinion_request"
OFFERED_NEWS_TOPIC_CATEGORIES_STATUS = "offered_news_topic_categories"

NEWS_GIVEN = "offered_news_details"
WHAT_TYPE_OF_NEWS = ["What other kinds of news would you want to discuss?",
                     "What are the other kinds of news would you like to hear about?",
                     "What else would you want to hear news about?",
                     "What type of news do you prefer?"]

NEWS_DUPLICATES = WHAT_TYPE_OF_NEWS


def skill_trigger_phrases():
    return [OFFER_BREAKING_NEWS]


def is_breaking_news_requested(prev_bot_utt, user_utt):
    if OFFER_BREAKING_NEWS.lower() in prev_bot_utt.get('text', '').lower():
        if is_yes(user_utt):
            return True
    return False
