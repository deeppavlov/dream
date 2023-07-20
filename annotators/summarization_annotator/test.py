import requests
from os import getenv


SUMMARIZATION_SERVICE_URL = getenv("SUMMARIZATION_SERVICE_URL")


def test_skill():
    url = "http://0.0.0.0:8171/respond"

    if SUMMARIZATION_SERVICE_URL == "http://brio-summarizer:8172/respond_batch":
        input_data = {"dialog": ["Good morning!",
                                 "Hi, this is a Dream Socialbot! How is the day going so far for you?",
                                 "Good! Can you tell me something about cooking and baking?",
                                 "Sure! Baking cookies is comforting, and cookies are the sweetest "
                                 "little bit of comfort food. Do you like cooking?",
                                 "It depends on my mood.",
                                 "May I recommend you a meal to try to practice cooking?",
                                 "No. Better tell me what do you have in mind?",
                                 "I've recently found a couple easy and healthy meals. How about cooking quinoa with "
                                 "turkey and broccoli?",
                                 "That sounds like a healthy and tasty meal! Quinoa is a great source of protein, and "
                                 "when paired with lean turkey and broccoli, it's a well-rounded and balanced meal.",
                                 "I am glad for you! I listened to my favorite music all day. "
                                 "Such a great thing you know! Has anything extraordinary happened today?",
                                 "I can tell you more about what made your day great or we can just chat?"
                                 "I'm happy to listen!"]}

        desired_output = ["a Dream Socialbot talks to users about cooking and baking cookies. The bot says cookies "
                          "are comforting, and baking them is a good way to feel good. The robot is called a "
                          "Dream Social bot. It is designed to talk to users in a friendly, conversational manner."]
    else:
        input_data = {"dialog": ["Привет! У тебя есть хобби?",
                                 "Мое хобби — кулинария.",
                                 "Здорово! А ты любишь готовить?",
                                 "Ага, я могу отлично приготовить разные блюда.",
                                 "Ты собираешь кулинарные рецепты?",
                                 "Да, уже есть большая коллекция.",
                                 "А какая национальная кухня тебе нравится?",
                                 "Конечно, русская.",
                                 "Русские блюда очень оригинальные, вкусные и полезные.",
                                 "А что ты любишь готовить больше всего?",
                                 "Я люблю готовить мясные блюда. Так что приглашаю в гости!"]}

        desired_output = ["У тебя есть хобби — кулинария, а у тебя есть большая коллекция кулинарных рецептов. Bot: Я "
                          "собираю кулинарные рецепты, собираю кулинарные рецепты, собираю кулинарные рецепты."]

    result = requests.post(url, json=input_data).json()
    assert result == [{"bot_attributes": {"summarized_dialog": desired_output[0]}}]
    print("SUCCESS!")


if __name__ == "__main__":
    test_skill()
