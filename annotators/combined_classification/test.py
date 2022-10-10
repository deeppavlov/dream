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
            "sentences": ["why you are so dumb"],
            "task": "emotion_classification",
            "answers_bert": [["anger"]],
            "multilabel": True
        },
        {
            "sentences_with_history": ["this is the best dog [SEP] so what you think"],
            "sentences": ["so what you think"],
            "task": "midas_classification",
            "answers_bert": [["open_question_opinion"]],
        },
        {"sentences": ["movies"], "task": "deeppavlov_topics", "answers_bert": [["Movies_TV"]]},
        {
            "sentences": ["you son of the bitch", "yes"],
            "task": "toxic_classification",
            "answers_bert": [["insult", "obscene", "toxic"], []],
            "multilabel": True
        },
        {
            "sentences": ["let's talk about movies"],
            "task": "cobot_dialogact_topics",
            "answers_bert": [["Entertainment_Movies"]],
            "multilabel": True
        },
        {"sentences": ["let's talk about games"], 
         "task": "cobot_topics",
         "answers_bert": [["Games"]], 
         "multilabel": True},
        {
            "sentences_with_history": ["What is the capital of Great Britain" \
                                       " [SEP] I don't know"],
            "sentences": ["I don't know"],
            "task": "cobot_dialogact_intents",
            "answers_bert": [["Information_DeliveryIntent"]],
            "multilabel":True
        },
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
            if config.get("multilabel", False):  # multilabel_task
                predicted_classes = [class_ for class_ in response if response[class_] > 0.5]
            else:
                predicted_classes = [class_ for class_ in response if response[class_] == max(response.values())]
            assert sorted(answer) == sorted(predicted_classes), " * ".join(
                [str(j) for j in [sentence, config["task"], answer, predicted_classes, response]]
                )
    logging.info("SUCCESS!")
    print("SUCCESS!")
    return 0


main_test()
