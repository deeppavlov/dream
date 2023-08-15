import requests
import json
from os import getenv


SERVICE_PORT = getenv("SERVICE_PORT")


def main():
    with open("test_data.json", "r") as f:
        data = json.load(f)
    # To skip "Oh, and remember this dialog's id" that raises error due to absence of 'dialog_id' field in test_data.
    data["dialogs"][0]["human_utterances"].append(data["dialogs"][0]["human_utterances"][0])
    result = requests.post(f"http://0.0.0.0:{SERVICE_PORT}/respond", json=data).json()
    assert result[0][0] in ["program_y", "movie_tfidf_retrieval"], print(result)


if __name__ == "__main__":
    main()
