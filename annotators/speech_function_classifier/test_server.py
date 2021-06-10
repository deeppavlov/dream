import requests
import os


SERVICE_PORT = os.getenv("SERVICE_PORT")
URL = f"http://0.0.0.0:{SERVICE_PORT}/model"


def handler(requested_data):
    hypothesis = requests.post(URL, json=requested_data).json()
    return hypothesis


def run_test(handler):
    hypothesis = handler({'phrase': ['fine, thank you.', 'and you?'], 'prev_phrase': 'How are you doing today?',
                          'prev_speech_function': 'React.Respond.Develop.Extend'})
    print(f"test name: {hypothesis}")
    assert hypothesis == [['React.Respond.Reply.Accept', 'React.Respond.Develop.Extend']]
    print("Success")


if __name__ == "__main__":
    run_test(handler)
