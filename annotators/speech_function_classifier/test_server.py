import requests
import os


SERVICE_PORT = os.getenv("SERVICE_PORT")
URL = f"http://0.0.0.0:{SERVICE_PORT}/model"


def handler(requested_data):
    hypothesis = requests.post(URL, json=requested_data).json()
    return hypothesis


def run_test(handler):
    hypothesis = handler({"bot_utterance": "hi", "human_utterance": "how are you"})
    print(f"test name: {hypothesis}")
    assert hypothesis == [{'type': 'React.Rejoinder.Support.Track.Clarify', 'confidence': 0.2331162013066703}]
    print("Success")


if __name__ == "__main__":
    run_test(handler)
