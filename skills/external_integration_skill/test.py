import requests

SERVICE_PORT = 8171


def test_respond():
    url = f"http://0.0.0.0:{SERVICE_PORT}/respond"
    result = requests.post(
        url,
        json={"sentences": ["hi", ""], "dialog_ids": ["7379921", None]},
    ).json()
    assert result == [["Success!", 0.9], ["", 0.0]], print(f"Got result: {result}, something is wrong.")
    print("Success!")


if __name__ == "__main__":
    test_respond()
