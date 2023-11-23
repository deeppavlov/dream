import requests
from os import getenv


SUMMARIZATION_SERVICE_URL = getenv("SUMMARIZATION_SERVICE_URL")


def test_skill():
    url = "http://0.0.0.0:8058/respond"

    if SUMMARIZATION_SERVICE_URL == "http://dialog-summarizer:8059/respond_batch":
        input_data = {
            "dialogs": [
                [
                    "Hi, my name is Mark!",
                    "Good morning, Mark! How can I assist you today?",
                    "Let's talk about cooking.",
                    "Sure! What is your favourite type of cuisine to cook or experiment with in the " "kitchen?",
                    "I like a wide range of cooking styles, such as Italian, Chinese, French and many " "more.",
                    "May I recommend you any Italian dish?",
                    "No. Better tell me what do you have in mind?",
                    "I've recently found a couple easy and healthy meals. How about cooking quinoa with "
                    "turkey and broccoli?",
                    "That sounds like a healthy and tasty meal! Quinoa is a great source of protein, and "
                    "when paired with lean turkey and broccoli, it's a well-rounded and balanced meal.",
                    "I am glad for you! I listened to my favorite music all day. "
                    "Such a great thing you know! Has anything extraordinary happened today?",
                    "I can tell you more about what made your day great or we can just chat?" "I'm happy to listen!",
                ]
            ],
            "previous_summaries": [""],
        }

        desired_output = [
            "Bot wants to know what is Mark's favorite type of cuisine to cook. Mark likes Italian, "
            "Chinese, French and many other cooking styles."
        ]
    else:
        input_data = {
            "dialogs": [
                [
                    "Привет! У тебя есть хобби?",
                    "Мое хобби — кулинария.",
                    "Здорово! А ты любишь готовить?",
                    "Ага, я могу отлично приготовить разные блюда.",
                    "Ты собираешь кулинарные рецепты?",
                    "Да, уже есть большая коллекция.",
                    "А какая национальная кухня тебе нравится?",
                    "Конечно, русская.",
                    "Русские блюда очень оригинальные, вкусные и полезные.",
                    "А что ты любишь готовить больше всего?",
                    "Я люблю готовить мясные блюда. Так что приглашаю в гости!",
                ]
            ],
            "previous_summaries": [""],
        }

        desired_output = [
            "У тебя есть хобби — кулинария, а у тебя есть большая коллекция кулинарных рецептов. Bot: Я "
            "собираю кулинарные рецепты, собираю кулинарные рецепты, собираю кулинарные рецепты."
        ]

    result = requests.post(url, json=input_data).json()

    assert result == [{"bot_attributes": {"summarized_dialog": desired_output[0]}}]
    print("SUCCESS!")


if __name__ == "__main__":
    test_skill()
