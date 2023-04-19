import requests


def test_skill():
    url = "http://0.0.0.0:8154/respond_batch"

    input_data = {"sentences": [""]}
    desired_output = [""]

    result = requests.post(url, json=input_data).json()[0]['batch']

    assert result == desired_output
    print("SUCCESS!")


if __name__ == "__main__":
    test_skill()
