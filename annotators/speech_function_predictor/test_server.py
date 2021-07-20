import requests
import os


SERVICE_PORT = os.getenv("SERVICE_PORT")
URL = f"http://0.0.0.0:{SERVICE_PORT}/model"


def handler(requested_data):
    hypothesis = requests.post(URL, json=requested_data).json()
    return hypothesis


def run_test(handler):
    hypothesis = handler(["React.Respond.Reply.Accept", "React.Respond.Develop.Extend"])
    print(f"test name: {hypothesis}")
    assert hypothesis[0][0] == [{}]
    assert {h["prediction"] for h in hypothesis[0][1]} == {
        "Sustain.Continue.Prolong.Elaborate",
        "React.Respond.Reply.Agree",
        "Sustain.Continue.Prolong.Enhance",
        "Sustain.Continue.Prolong.Extend",
        "React.Rejoinder.Track.Confirm",
    }
    print("Success")


if __name__ == "__main__":
    run_test(handler)
