import requests


def test_respond():
    url = "http://0.0.0.0:8122/respond"

    texts = ["Chris was bad at _.", "Chris was _ so he could not come."]

    request_data = {"texts": texts}

    result = requests.post(url, json=request_data).json()

    assert result["infilled_text"][0].startswith("Chris was bad at"), print(
        f"Got\n{result}\n, but had to be starting with 'Chris was bad at math'"
    )
    assert result["infilled_text"][1].startswith("Chris was") and result["infilled_text"][1].endswith(
        "so he could not come."
    ), print(f"Got\n{result}\n, but had to be ending with 'so he could not come.'")
    print("Success")


if __name__ == "__main__":
    test_respond()
