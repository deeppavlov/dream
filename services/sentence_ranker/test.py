import requests


def test_respond():
    url = "http://0.0.0.0:8128/respond"

    sentence_pairs = [
        ["Привет! Как дела?", "хорошо. а у тебя как дела?"],
        ["Привет! Как дела?", "какой твой любимый фильм?"],
        ["Какой твой любимый фильм?", "Гордость и предубеждение"],
        ["Какой твой любимый фильм?", "пересматриваю Гордость и предубеждение иногда."],
        ["Какой твой любимый фильм?", "я люблю играть в компьютерные игры."],
    ]

    gold = [0.8988315, 0.62241143, 0.65046525, 0.54038674, 0.48419473]

    request_data = {"sentence_pairs": sentence_pairs}
    result = requests.post(url, json=request_data).json()[0]["batch"]
    for i, score in enumerate(result):
        assert score != 0.0, f"Expected:{gold[i]}\tGot\n{score}"
    print("Success!")


if __name__ == "__main__":
    test_respond()
