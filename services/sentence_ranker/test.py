import requests


def test_respond():
    url = "http://0.0.0.0:8122/respond"

    contexts = ["Привет! Как дела?", "Привет! Как дела?", "Какой твой любимый фильм?", "Какой твой любимый фильм?"]
    hypotheses = [
        "хорошо. а у тебя как дела?",
        "какой твой любимый фильм?",
        "пересматриваю Гордость и предубеждение иногда.",
        "я люблю играть в компьюетрные игры.",
    ]
    gold = [0.334246, 0.33038276, 0.40354252, 0.3839873]

    request_data = {"dialog_contexts": contexts, "hypotheses": hypotheses}
    result = requests.post(url, json=request_data).json()[0]["batch"]
    print(result)
    for i, score in enumerate(result):
        assert round(score, 4) == round(gold[i], 4), f"Expected:{gold[i]}\tGot\n{score}"
    print("Success!")


if __name__ == "__main__":
    test_respond()
