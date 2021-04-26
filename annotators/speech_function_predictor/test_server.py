import requests
import os


SERVICE_PORT = os.getenv("SERVICE_PORT")
URL = f"http://0.0.0.0:{SERVICE_PORT}/model"


def handler(requested_data):
    hypothesis = requests.post(URL, json=requested_data).json()
    return hypothesis


def run_test(handler):
    hypothesis = handler(["Reply.Acknowledge"])
    print(f"test name: {hypothesis}")
    assert hypothesis == [{}]
    print("Success")


if __name__ == "__main__":
    run_test(handler)
