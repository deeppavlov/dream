import requests


def test_respond():
    url = "http://0.0.0.0:8091/respond"

    contexts = ["Привет! Как дела?", "Какой твой любимый фильм?"]
    hypotheses = [
        ["хорошо. а у тебя как дела?", "какой твой любимый фильм?"],
        ["пересматриваю Гордость и предубеждение иногда.", "я люблю играть в компьюетрные игры."],
    ]
    gold = [[0.334246, 0.33038276], [0.40354252, 0.3839873]]
    request_data = {"dialog_contexts": contexts, "hypotheses": hypotheses}
    result = requests.post(url, json=request_data).json()["scores"]
    print(result)
    assert len(result) == 3 and len(result[0]) > 0, f"Got\n{result}"
    print("Success!")


if __name__ == "__main__":
    test_respond()
