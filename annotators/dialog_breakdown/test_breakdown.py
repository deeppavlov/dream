import requests


def main():
    url = 'http://0.0.0.0:8082/model'

    request_data = {
        "context": ["There is a new thing for me about human world: The kicksled or spark is a small sled "
                    "consisting of a chair mounted on a pair of flexible metal runners that extend backward to about "
                    "twice the chair's length. Have you ever heard about it? no tell me about I misheard you. what's "
                    "it that you'd like to chat about? i don't know you pick a subject"],
        "curr_utterance": ["ya and apparently dolphins can communicate with other dolphins over the phone "
                           "and know who they are talking to"]
    }

    print(requests.post(url, json=request_data).json())
    bd_proba = requests.post(url, json=request_data).json()[0]["breakdown"]
    bd_proba = round(bd_proba, 3)
    assert bd_proba == 0.995, f'Got\n{bd_proba}\n, but expected:\n{0.995}'
    print('Success')


if __name__ == '__main__':
    main()
