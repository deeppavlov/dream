import requests


def main():
    url = "http://0.0.0.0:8126/respond"

    request_data = [{"utterances": ["i live in moscow"]}]

    for data in request_data:
        result = requests.post(url, json=data).json()
        print(result)


if __name__ == "__main__":
    main()
