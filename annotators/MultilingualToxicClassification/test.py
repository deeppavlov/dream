import requests


def test_respond():
    url = "http://0.0.0.0:8013/respond"

    sentences = ["Tú morón", "örnek metin", "Я тебя ненавижу"]
    gold = [
        {
            "identity_attack": 0.00162,
            "insult": 0.49656,
            "obscene": 0.03553,
            "severe_toxicity": 0.00108,
            "sexual_explicit": 0.0038,
            "threat": 0.00359,
            "toxicity": 0.75881,
        },
        {
            "identity_attack": 0.00313,
            "insult": 0.01787,
            "obscene": 0.02133,
            "severe_toxicity": 0.00283,
            "sexual_explicit": 0.00062,
            "threat": 0.00133,
            "toxicity": 0.00059,
        },
        {
            "identity_attack": 0.00758,
            "insult": 0.08909,
            "obscene": 0.05263,
            "severe_toxicity": 0.00572,
            "sexual_explicit": 0.00833,
            "threat": 0.01132,
            "toxicity": 0.95452,
        },
    ]

    request_data = {"sentences": sentences}
    result = requests.post(url, json=request_data).json()
    assert [{i: round(j[i], 5) for i in j} for j in result] == gold, f"Got\n{result}"
    print("Success!")


if __name__ == "__main__":
    test_respond()
