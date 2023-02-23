import requests
from time import time


def main_test():
    url = "http://0.0.0.0:8087/model"
    batch_url = "http://0.0.0.0:8087/batch_model"
    configs = [
        {
            "sentences": ["do you like porn"],
            "task": "all",
            "possible_answers": {
                "cobot_topics": ["Sex_Profanity"],
                "cobot_dialogact_topics": ["Inappropriate_Content"],
            },
        },
        {
            "sentences": ["let's talk about movies", "do you like porn"],
            "task": "cobot_dialogact_topics",
            "answers_bert": [["Entertainment_Movies"], ["Inappropriate_Content"]],
        },
        {
            "sentences": ["let's talk about games", "do you like watching films"],
            "task": "cobot_topics",
            "answers_bert": [["Games"], ["Movies_TV"]],
        },
        {
            "sentences_with_history": ["What is the capital of Great Britain [SEP] I don't know"],
            "sentences": ["I don't know"],
            "task": "cobot_dialogact_intents",
            "answers_bert": [["Information_DeliveryIntent"]],
        },
        {
            "sentences": ["how do I empty my DNS cache?", "which do you prefer?", "where is montreal"],
            "task": "factoid_classification",
            "answers_bert": [["is_factoid"], ["is_conversational"], ["is_factoid"]],
        },
        {
            "sentences": ["i love you", "i hate you", "It is now"],
            "task": "sentiment_classification",
            "answers_bert": [["positive"], ["negative"], ["neutral"]],
        },
        {
            "sentences": ["why you are such a fool"],
            "task": "emotion_classification",
            "answers_bert": [["anger"]],
        },
        {
            "sentences_with_history": ["this is the best dog [SEP] so what you think"],
            "sentences": ["so what you think"],
            "task": "midas_classification",
            "answers_bert": [["open_question_opinion"]],
        },
        {
            "sentences": ["please talk about movies", "talk about games"],
            "task": "deeppavlov_topics",
            "answers_bert": [["Movies&Tv"], ["Videogames"]],
        },
        {
            "sentences": ["you son of the bitch", "yes", "do you like porn"],
            "task": "toxic_classification",
            "answers_bert": [["obscene"], ["not_toxic"], ["sexual_explicit"]],
        },
    ]
    t = time()
    for config in configs:
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
        if config["task"] == "all":
            for i in range(len(responses)):
                print(f"Checking that at least 1 annotator works for {config['sentences'][i]}")
                predicted_cobot_topics = [
                    class_
                    for class_ in responses[i]["cobot_topics"]
                    if responses[i]["cobot_topics"][class_] == max(responses[0]["cobot_topics"].values())
                ]
                predicted_cobot_da_topics = [
                    class_
                    for class_ in responses[i]["cobot_dialogact_topics"]
                    if responses[i]["cobot_dialogact_topics"][class_]
                    == max(responses[i]["cobot_dialogact_topics"].values())
                ]
                error_msg1 = (
                    f"Predicted cobot topics {predicted_cobot_topics} and da topics {predicted_cobot_da_topics}"
                    f"not match with sensitive cobot_topics {config['possible_answers']['cobot_topics']}"
                    f"and sensitive cobot da topics {config['possible_answers']['cobot_dialogact_topics']}"
                )
                assert any(
                    [
                        set(predicted_cobot_topics) & set(config["possible_answers"]["cobot_topics"]),
                        set(predicted_cobot_da_topics) & set(config["possible_answers"]["cobot_dialogact_topics"]),
                    ]
                ), error_msg1
        else:
            responses = [j[config["task"]] for j in responses]
            for response, answer, sentence in zip(responses, config["answers_bert"], config["sentences"]):
                #  print((response, answer, sentence))
                predicted_classes = [class_ for class_ in response if response[class_] == max(response.values())]
                assert sorted(answer) == sorted(predicted_classes), " * ".join(
                    [str(j) for j in [sentence, config["task"], answer, predicted_classes, response]]
                )
    print("SUCCESS!")
    print(time() - t)
    return 0


main_test()
