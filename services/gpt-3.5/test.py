import os
import requests


N_HYPOTHESES_TO_GENERATE = int(os.environ.get("N_HYPOTHESES_TO_GENERATE", 1))


def test_respond():
    url = "http://0.0.0.0:8126/respond"
    contexts = [
        [
            "Hello, who are you?",
            "I am Marcus, your travel guide. How can I help you today?",
            "Where can I spend an evening in Beirut?",
            "You can catch a play at Baalbeck International Festival, or go for a sailing trip.",
            "Where can I have some fun in Goa?",
            "Goa has peaceful beaches and fun-filled pubs/clubs.",
            "Where should I go in Goa if I want to drink some cocktails?",
        ]
    ]
    result = requests.post(url, json={"utterances_histories": contexts}).json()
    assert [all(len(sample[0]) > 0 for sample in result)], f"Got\n{result}\n, something is wrong"
    print("Success")
    print(result)


if __name__ == "__main__":
    test_respond()
