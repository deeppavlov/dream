import requests


def test_respond():
    url = "http://0.0.0.0:3665/respond"

    sentences = ['Sei una testa di cazzo!!', 'Я боюсь тебя']
    gold = [{'anger': 0.99177, 'fear': 0.00091, 'joy': 0.00504, 'sadness': 0.00229},
            {'anger': 0.00115, 'fear': 0.99664, 'joy': 0.00081, 'sadness': 0.0014}]

    request_data = {"sentences": sentences}
    result = requests.post(url, json=request_data).json()
    assert [{i: round(j[i], 5) for i in j} for j in result] == gold, f"Got\n{result}"
    print("Success!")


if __name__ == "__main__":
    test_respond()
