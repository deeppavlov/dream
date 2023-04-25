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

    gold = [0.7672719955444336, 0.15072298049926758, 0.5039470791816711, 0.4652850031852722, 0.23436866700649261]

    request_data = {"sentence_pairs": sentence_pairs}
    result = requests.post(url, json=request_data).json()[0]["batch"]
    for i, score in enumerate(result):
        assert round(score, 2) == round(gold[i], 2), f"Expected:{gold[i]}\tGot\n{score}"
    print("Success!")


if __name__ == "__main__":
    test_respond()
