import requests


def test_respond():
    url = "http://0.0.0.0:8126/respond"

    sentences = ["иди в жопу", "иду иду"]
    gold = [0.9885, 0.0086]
    request_data = {"sentences": sentences}
    result = requests.post(url, json=request_data).json()
    assert round(result[0]["toxic"], 4) == gold[0] and round(result[1]["toxic"], 4) == gold[1], f"Got\n{result}"
    print("Success!")


if __name__ == "__main__":
    test_respond()
