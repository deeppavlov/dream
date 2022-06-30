import requests


def main():
    url = "http://0.0.0.0:8074/respond"

    request_data = [{"sentences": ["я ге видел малако"]}]

    gold_results = [["я не видел малакон"]]

    count = 0
    for data, gold_result in zip(request_data, gold_results):
        result = requests.post(url, json=data).json()
        if result == gold_result:
            count += 1

    assert count == len(request_data)
    print("Success")


if __name__ == "__main__":
    main()
