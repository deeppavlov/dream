import requests
import os

SERVICE_PORT = os.getenv("SERVICE_PORT")
URL = f"http://0.0.0.0:{SERVICE_PORT}/model"


def handler(requested_data):
    hypothesis = requests.post(URL, json=requested_data).json()
    return hypothesis


def run_test(handler):
    hypothesis = handler(["React.Respond.Reply.Accept", "React.Respond.Support.Develop.Extend"])
    print(f"test name: {hypothesis}")
    assert hypothesis[0][0] == [{}]
    assert {h["prediction"] for h in hypothesis[0][1]} == {
        "React.Respond.Support.Reply.Acknowledge",
        "Sustain.Continue.Prolong.Elaborate",
        "React.Rejoinder.Support.Track.Confirm",
        "React.Respond.Confront.Reply.Contradict",
        "React.Respond.Confront.Reply.Disagree",
        "Sustain.Continue.Prolong.Enhance",
        "React.Rejoinder.Support.Track.Clarify",
        "React.Respond.Support.Reply.Agree",
        "React.Respond.Confront.Reply.Disawow",
        "React.Respond.Support.Reply.Affirm",
        "Sustain.Continue.Prolong.Extend",
        "React.Rejoinder.Support.Track.Check",
    }

    print("Success")


if __name__ == "__main__":
    run_test(handler)
