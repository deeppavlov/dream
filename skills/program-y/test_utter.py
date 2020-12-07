import pprint

import requests


def main_test():
    url = "http://0.0.0.0:3005/api/rest/v1.0/ask"
    while True:
        sent = input("Write down your request:")
        data = {"sentences_batch": [[sent]]}
        response = requests.post(url, json=data).json()
        print(f"---\nQ: {sent}\nA: {response[0][0]} \ndata: {pprint.pformat(response)}")


if __name__ == "__main__":
    main_test()
