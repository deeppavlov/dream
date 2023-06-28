import requests

SERVICE_PORT = 8198


def test_respond():
    url = f"http://0.0.0.0:{SERVICE_PORT}/respond"
    result = requests.post(
        url,
        json={
            "dialogs": [
                {
                    "dialog_id": "11b8940f99738c4d92d54076daab4bb6",
                    "payload": "hi",
                }
            ]
        },
    ).json()
    assert result == {"response": "Success!", "confidence": 0.9}, print(f"Got result: {result}, something is wrong.")
    print("Success!")


if __name__ == "__main__":
    test_respond()
