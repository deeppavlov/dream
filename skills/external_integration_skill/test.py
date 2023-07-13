import requests

SERVICE_PORT = 8168


def test_respond():
    url = f"http://0.0.0.0:{SERVICE_PORT}/respond"
    result = requests.post(
        url,
        json={
            "dialogs": [
                {
                    "dialog_id": "11b8940f99738c4d92d54076daab4bb6",
                    "human_utterances": [{"text": "hi"}],
                },
                {
                    "dialog_id": None,
                    "human_utterances": [{"text": ""}],
                }
            ]
        },
    ).json()
    print(result)
    assert result == [["", 0.8], ["Success!", 0.9]], print(f"Got result: {result}, something is wrong.")
    print("Success!")


if __name__ == "__main__":
    test_respond()
