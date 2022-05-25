import requests


def test_respond():
    url = "http://0.0.0.0:8122/respond"

    text = ["Chris was bad at _.", "Chris was _ so he could not come."]

    request_data = {"text": text}

    result = requests.post(url, json=request_data).json()

    assert result["predicted_tokens"][0].startswith(
        "Chris was bad at"
    ), f"Got\n{result}\n, but had to be starting with 'Chris was bad at math'"
    assert result["predicted_tokens"][1].startswith("Chris was") and result["predicted_tokens"][1].endswith(
        "so he could not come."
    )
    print("Success")


if __name__ == "__main__":
    test_respond()
