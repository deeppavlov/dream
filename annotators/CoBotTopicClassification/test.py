import requests


def main():
    url = "http://0.0.0.0:8000/topics"

    request_data = {"sentences": [["do you like muslims?", "what are your thoughts about donald trump?"]]}

    result = requests.post(url, json=request_data).json()
    gold_result = [[["Religion", "Politics"]]]

    assert result == gold_result, f"Got\n{result}\n, but expected:\n{gold_result}"
    print("Success")


if __name__ == "__main__":
    main()
