import requests
import json


def main():
    url = "http://0.0.0.0:8106/respond"

    request_data = json.load(open("test_input.json"))  # list of one dialog

    result = requests.post(url, json={"dialogs": request_data}).json()
    gold_result = json.load(open("test_output.json"))

    assert "response" in result[0] and result[0]["facts"][0]["entity"] == "michael jordan", print(
        f"Got\n{result}\n, but expected:\n{gold_result}"
    )

    print("Success")


if __name__ == "__main__":
    main()
