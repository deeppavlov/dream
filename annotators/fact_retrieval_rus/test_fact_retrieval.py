import requests


def main():
    url = "http://0.0.0.0:8127/model"

    request_data = [
        {
            "sentences": ["Какая столица России?"],
            "entity_substr": [["россии"]],
            "entity_tags": [["loc"]],
            "entity_pages": [[["Россия"]]],
        }
    ]

    gold_results = [["Москва"]]

    for data, gold_result in zip(request_data, gold_results):
        result = requests.post(url, json=data).json()

    print("Success")


if __name__ == "__main__":
    main()
