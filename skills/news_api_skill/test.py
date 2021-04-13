from common.news import get_news_about_topic

NEWS_API_SKILL_URL = "http://0.0.0.0:8066/respond"
result = get_news_about_topic("example", NEWS_API_SKILL_URL)

assert result and result[1] == 1. and result[4]["curr_news"] and result[4]["news_topic"] == "example", print(result)
