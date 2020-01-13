import requests


def main_test():
    url = 'http://0.0.0.0:8008/api/rest/v1.0/ask'

    sent = "do you have a boyfriend"
    data = {"sentences_batch": [[sent]]}
    response = requests.post(url, json=data).json()[0][0]
    assert "I'm happily single. But if you know any nice guys, let me know!" in response, print(sent, '.', response)

    sentences = ['can you sing', 'can you sing me a song']
    for sent in sentences:
        data = {"sentences_batch": [[sent]]}
        response = requests.post(url, json=data).json()[0][0]
        assert "Daisy, Daisy" in response, print(sent, '.', response)

    sentences = ["let's talk about you", 'tell me about yourself']
    for sent in sentences:
        data = {"sentences_batch": [[sent]]}
        response = requests.post(url, json=data).json()[0][0]
        assert "The DNA of who" in response, print(sent, '.', response)


if __name__ == '__main__':
    main_test()
