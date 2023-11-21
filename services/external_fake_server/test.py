import requests


def main():
    url = "http://0.0.0.0:8169/return_response"

    request_datas = [
        {"dialog_id": "jknvawoioqb783HGGIUUGI", "payload": "How are you doing?"},
        {"dialog_id": None, "payload": ""},
    ]
    gold_results = [
        {"response": "Success!", "confidence": 0.9},
        {"response": "", "confidence": 0.0},
    ]
    i = 0
    for request_data in request_datas:
        result = requests.post(url, json=request_data).json()
        assert result == gold_results[i], print(f"Got result: {result}, something is wrong.")
        i += 1
    print("Success!")


if __name__ == "__main__":
    main()
