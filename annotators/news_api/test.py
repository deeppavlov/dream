from common.news import get_news_about_topic

NEWS_API_ANNOTATOR_URL = "http://0.0.0.0:8112/respond"
result = get_news_about_topic("example", NEWS_API_ANNOTATOR_URL)

assert result["title"] and len(result["title"]) > 0, print(result)

print("SUCCESS")
