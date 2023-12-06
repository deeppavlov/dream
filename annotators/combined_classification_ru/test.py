import requests
from time import time


def main_test():
    url = "http://0.0.0.0:8198/model"
    batch_url = "http://0.0.0.0:8198/batch_model"
    configs = [
        {
            "sentences": ["поговорим о книгах", "ты любишь порно"],
            "task": "topics_ru",
            "answers_bert": [["литература"], ["секс"]],
        },
        {
            "sentences": ["что ты любишь", "где монреаль"],
            "task": "factoid_classification",
            "answers_bert": [["is_conversational"], ["is_factoid"]],
        },
        {
            "sentences": ["я тебя люблю", "я тебя ненавижу", "сейчас"],
            "task": "sentiment_classification",
            "answers_bert": [["positive"], ["negative"], ["neutral"]],
        },
        {
            "sentences": ["почему ты такой дурак"],
            "task": "emotion_classification",
            "answers_bert": [["anger"]],
        },
        {
            "sentences_with_history": ["это лучшая собака [SEP] да, много"],
            "sentences": ["да, много"],
            "task": "midas_classification",
            "answers_bert": [["pos_answer"]],
        },
        {
            "sentences": ["привет", "и вот таких уродов дахуя"],
            "task": "toxic_classification",
            "answers_bert": [["not_toxic"], ["toxic"]],
        },
    ]
    t = time()
    for config in configs:
        print(config)
        if "sentences_with_history" in config:
            config["utterances_with_histories"] = [[k] for k in config["sentences_with_history"]]
        else:
            config["utterances_with_histories"] = [[k] for k in config["sentences"]]
        responses = requests.post(url, json=config).json()
        batch_responses = requests.post(batch_url, json=config).json()
        batch_error_msg = f"Batch responses {batch_responses} not match to responses {responses}"
        assert (
            batch_responses[0]["batch"][0]["toxic_classification"] == responses[0]["toxic_classification"]
        ), batch_error_msg
        responses = [j[config["task"]] for j in responses]
        for response, answer, sentence in zip(responses, config["answers_bert"], config["sentences"]):
            print((response, answer, sentence))
            predicted_classes = [class_ for class_ in response if response[class_] == max(response.values())]
            assert sorted(answer) == sorted(predicted_classes), " * ".join(
                [str(j) for j in [sentence, config["task"], answer, predicted_classes, response]]
            )
    print("SUCCESS!")
    print(time() - t)
    return 0


main_test()
