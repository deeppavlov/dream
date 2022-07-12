import requests


def test_respond():
    url = "http://0.0.0.0:3668/respond"

    sentences = ['Hola! Como estas?', 'örnek metin', 'Болван несчастный']
    gold = [{'Negative': 0.0274, 'Neutral': 0.706, 'Positive': 0.2666}, {'Negative': 0.29077, 'Neutral': 0.33038, 'Positive': 0.37885},
            {'Negative': 0.94606, 'Neutral': 0.03936, 'Positive': 0.01458}]
    request_data = {"sentences": sentences}
    result = requests.post(url, json=request_data).json()
    assert [{i: round(j[i], 5) for i in j} for j in result] == gold, f"Got\n{result}"
    print("Success!")


if __name__ == "__main__":
    test_respond()
