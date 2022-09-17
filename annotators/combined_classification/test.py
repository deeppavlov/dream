import requests
import logging


def main_test():
    url = "http://0.0.0.0:8087/model"
    batch_url = "http://0.0.0.0:8087/batch_model"
    configs = [
        {
            "sentences": ["how do I empty my DNS cache?", "which do you prefer?"],
            "task": "factoid_classification",
            "answers_bert": [["is_factoid"], ["is_conversational"]],
        },
        {
            "sentences": ["i love you", "i hate you", "It is now"],
            "task": "sentiment_classification",
            "answers_bert": [["positive"], ["negative"], ["neutral"]],
        },
        {
            "sentences": ["you son of the bitch", "yes"],
            "task": "toxic_classification",
            "answers_bert": [["obscene"], ["not_toxic"]],
        },
        {
            "sentences": ["why you are so dumb"],
            "task": "emotion_classification",
            "answers_bert": [["anger"]],
        },
        {
            "sentences_with_history": ["this is the best dog [SEP] so what you think ha"],
            "sentences": ["so what you think ha"],
            "task": "midas_classification",
            "answers_bert": [["open_question_opinion"]],
        },
        {"sentences": ["books"], "task": "topics_classification", "answers_bert": [["Books&Literature"]]},
    ]
    for config in configs:
        if "sentences_with_history" in config:
            config["utterances_with_histories"] = [[k] for k in config["sentences_with_history"]]
        else:
            config["utterances_with_histories"] = [[k] for k in config["sentences"]]
        responses = requests.post(url, json=config).json()
        batch_responses = requests.post(batch_url, json=config).json()
        assert batch_responses[0]["batch"] == responses, (
            f"Batch responses {batch_responses} " f"not match to responses {responses}"
        )
        responses = [j[config["task"]] for j in responses]
        for response, answer, sentence in zip(responses, config["answers_bert"], config["sentences"]):
            print(response)
            predicted_classes = [class_ for class_ in response if response[class_] == max(response.values())]
            assert sorted(answer) == sorted(predicted_classes), " * ".join(
                [str(j) for j in [sentence, config["task"], answer, predicted_classes, response]]
            )
    logging.info("SUCCESS!")
    return 0


main_test()
