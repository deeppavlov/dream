import requests


def main_test():
    url = 'http://0.0.0.0:8022/api/rest/v1.0/ask'
    sentences = ['fuck you', 'you suck', 'I hate you']
    for sent in sentences:
        data = {"sentences_batch": [[sent]]}
        response = requests.post(url, json=data).json()[0][0]
        assert "Let me tell you something you already know." in response, print(sent, '.', response)


if __name__ == '__main__':
    main_test()
