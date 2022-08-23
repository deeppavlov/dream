import requests


def test_respond():
    url = "http://0.0.0.0:8128/respond"

    sentence_pairs = [
        ["Привет! Как дела?", "хорошо. а у тебя как дела?"],
        ["Привет! Как дела?", "какой твой любимый фильм?"],
        ["Какой твой любимый фильм?", "пересматриваю Гордость и предубеждение иногда."],
        ["Какой твой любимый фильм?", "я люблю играть в компьютерные игры."]
    ]

    gold = [0.334246, 0.33038276, 0.40354252, 0.3839873]

    request_data = {"sentence_pairs": sentence_pairs}
    result = requests.post(url, json=request_data).json()[0]["batch"]
    print(result)
    for i, score in enumerate(result):
        assert round(score, 4) == round(gold[i], 4), f"Expected:{gold[i]}\tGot\n{score}"
    print("Success!")


if __name__ == "__main__":
    test_respond()
