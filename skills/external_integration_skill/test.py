import requests
from os import getenv

SERVICE_PORT = 8888


def test_respond():
    url = f"http://0.0.0.0:{SERVICE_PORT}/respond"
    result = requests.post(
        url,
        json={
            "dialogs": [
                {
                    "dialog_id": "11b8940f99738c4d92d54076daab4bb6",
                    "human_utterances": [{"text": "hi"}],
                }
            ]
        },
    ).json()
    print(result)

    assert len(result) and [
        all(len(sample[0]) > 0 for sample in result)
    ], f"Got\n{result}\n, something is wrong"
    print("Success!")


if __name__ == "__main__":
    test_respond()
