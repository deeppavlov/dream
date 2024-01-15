import requests
import os


SERVICE_PORT = os.getenv("SERVICE_PORT")
URL = f"http://0.0.0.0:{SERVICE_PORT}"


def run_test():
    model_test_data = {
        "phrases": ["fine, thank you. and you?"],
        "prev_phrases": ["How are you doing today?"],
        "prev_speech_functions": ["Open.Demand.Fact"],
    }
    model_hypothesis = requests.post(f"{URL}/respond", json=model_test_data).json()

    print("test name: sfc model_hypothesis")
    assert model_hypothesis == ["React.Rejoinder.Support.Response.Resolve"], print(model_hypothesis)

    annotation_test_data = {
        "phrases": ["fine, thank you.", "and you?"],
        "prev_phrases": ["How are you doing today?", "How are you doing today?"],
        "prev_speech_functions": ["Open.Demand.Fact", "Open.Demand.Fact"],
    }

    annotation_hypothesis = requests.post(f"{URL}/respond_batch", json=annotation_test_data).json()

    print("test name: sfc annotation_hypothesis")
    assert annotation_hypothesis == [
        {"batch": ["React.Rejoinder.Support.Response.Resolve", "React.Rejoinder.Support.Track"]}
    ], print(annotation_hypothesis)

    print("Success")


if __name__ == "__main__":
    run_test()
