import requests


def test_respond():
    url = "http://0.0.0.0:8128/respond"

    sentence_pairs = [
        ["Hi! How are you?", "Good. How are you?"],
        ["Hi! How are you?", "what's your favorite movie?"],
        ["What's your favorite movie?", "Pride and Prejudice"],
        ["What's your favorite movie?", "I watch Pride and Prejudice sometimes."],
        ["What's your favorite movie?", "I like to play computer games."],
    ]

    gold = [0.8988315, 0.62241143, 0.65046525, 0.54038674, 0.48419473]

    request_data = {"sentence_pairs": sentence_pairs}
    result = requests.post(url, json=request_data).json()[0]["batch"]
    for i, score in enumerate(result):
        assert round(score, 2) == round(gold[i], 2), f"Expected:{gold[i]}\tGot\n{score}"
    print("Success!")


if __name__ == "__main__":
    test_respond()
