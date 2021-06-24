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
    assert hypothesis == [[[{}], [{'prediction': 'Sustain.Continue.Prolong.Elaborate',
                                   'confidence': 0.1896551724137931},
                                  {'prediction': 'React.Respond.Reply.Agree',
                                   'confidence': 0.13793103448275862},
                                  {'prediction': 'Sustain.Continue.Prolong.Enhance',
                                   'confidence': 0.10344827586206896},
                                  {'prediction': 'React.Rejoinder.Track.Confirm',
                                   'confidence': 0.08620689655172414},
                                  {'prediction': 'Sustain.Continue.Prolong.Extend',
                                   'confidence': 0.08620689655172414}]]]
    print("Success")


if __name__ == "__main__":
    run_test(handler)
