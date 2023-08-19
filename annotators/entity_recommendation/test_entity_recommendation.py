import requests
import json


def main():
    url = "http://0.0.0.0:8095/model"

    with open('test_request.json', 'r') as f:
        test_request = json.load(f)

    with open('test_response.json', 'r') as f:
        test_response = json.load(f)

    result = requests.post(url, json=test_request).json()
    assert result == test_response, f'Result is not equals to test_response {result}'
    print("Success")


if __name__ == "__main__":
    main()
