import requests


def main():
    url = "http://0.0.0.0:8130/respond"

    request_data = [{"utterances": [["In Italy it is always a nosh-up. Is there any italian dish that you never get tired of eating?", "spaghetti."]]}]

    count = 0
    for data in request_data:
        result = requests.post(url, json=data).json()
        print(result)


if __name__ == "__main__":
    main()
