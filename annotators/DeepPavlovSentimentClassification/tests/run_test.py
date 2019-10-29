import requests


def get_input_json(text: str):
    return {"sentences": [text]}


selected_classes = ["neutral", "positive", "negative"]


def test_one_step_responses():
    url = "http://0.0.0.0:8024/sentiment_annotations"
    input_data = {"sentences": ["ok", "i love you", "i hate you"]}
    response = requests.post(url, json=input_data).json()
    for tgt, pred in zip(selected_classes, response):
        assert tgt == pred[0][0]
    print("SUCCESS!")


if __name__ == "__main__":
    test_one_step_responses()
