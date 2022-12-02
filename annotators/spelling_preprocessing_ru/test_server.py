import requests
import os

config_name = os.getenv("CONFIG")


def main():

    url = "http://0.0.0.0:8074/respond"
    if config_name == "levenshtein_corrector_ru.json":
        request_data = [{"sentences": ["я ге видел малако"]}]

        gold_results = [["я не видел малакон"]]

    else:
        request_data = [{"sentences": ["tge shop is cloed"]}]

        gold_results = [["the shop is closed"]]

    count = 0
    for data, gold_result in zip(request_data, gold_results):
        result = requests.post(url, json=data).json()
        if result == gold_result:
            count += 1

    assert count == len(request_data)
    print("Success")


if __name__ == "__main__":
    main()
