import requests
import os


SERVICE_PORT = os.getenv("SERVICE_PORT")
URL = f"http://0.0.0.0:{SERVICE_PORT}"
MODEL_URL = f"{URL}/model"
ANNOTATION_URL = f"{URL}/annotation"


def run_test():
    model_test_data = {
        "phrase": ["fine, thank you.", "and you?"],
        "prev_phrase": "How are you doing today?",
        "prev_speech_function": "Open.Demand.Fact",
    }
    model_hypothesis = requests.post(MODEL_URL, json=model_test_data).json()

    print("test name: sfc model_hypothesis")
    assert model_hypothesis == [
        [
            "React.Rejoinder.Support.Response.Resolve",
            "React.Rejoinder.Confront.Response.Re-challenge",
        ]
    ]

    annotation_test_data = [
        {
            "phrase": "fine, thank you. and you?",
            "prev_phrase": "How are you doing today?",
            "prev_speech_function": "Open.Demand.Fact",
        }
    ]
    annotation_hypothesis = requests.post(ANNOTATION_URL, json=annotation_test_data).json()

    print("test name: sfc annotation_hypothesis")
    assert annotation_hypothesis == [
        {
            "batch": [
                [
                    "React.Rejoinder.Support.Response.Resolve",
                    "React.Rejoinder.Confront.Response.Re-challenge",
                ]
            ]
        }
    ]

    print("Success")


if __name__ == "__main__":
    run_test()
