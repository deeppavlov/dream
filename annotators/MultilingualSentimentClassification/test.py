import requests


def test_respond():
    url = "http://0.0.0.0:8024/respond"

    sentences = ["Hola! Como estas?", "örnek metin", "Болван несчастный"]
    gold = [
        {"negative": 0.0274, "neutral": 0.706, "positive": 0.2666},
        {"negative": 0.29077, "neutral": 0.33038, "positive": 0.37885},
        {"negative": 0.94606, "neutral": 0.03936, "positive": 0.01458},
    ]
    request_data = {"sentences": sentences}
    result = requests.post(url, json=request_data).json()
    assert [{i: round(j[i], 5) for i in j} for j in result] == gold, f"Got\n{result}"
    print("Success!")


if __name__ == "__main__":
    test_respond()
