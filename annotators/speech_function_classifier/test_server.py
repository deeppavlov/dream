import requests
import os


SERVICE_PORT = os.getenv("SERVICE_PORT")
URL = f"http://0.0.0.0:{SERVICE_PORT}/model"


def handler(requested_data):
    hypothesis = requests.post(URL, json=requested_data).json()
    return hypothesis


def run_test(handler):
    hypothesis = handler(
        {
            "phrase": ["fine, thank you.", "and you?"],
            "prev_phrase": "How are you doing today?",
            "prev_speech_function": "Open.Demand.Fact",
        }
    )
    print(f"test name: {hypothesis}")
    assert hypothesis == [["Open.Give.Fact", "React.Rejoinder.Confront.Response.Re-challenge"]]
    print("Success")


if __name__ == "__main__":
    run_test(handler)
