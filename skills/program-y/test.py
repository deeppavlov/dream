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

    sentences = ["can i ask you a question", 'i have a question for you', 'i have a question']
    for sent in sentences:
        data = {"sentences_batch": [[sent]]}
        response = requests.post(url, json=data).json()[0][0]
        assert "You can ask me anything" in response, print(sent, '.', response)

    sentences = ["ask me a question", 'do you wanna ask me a question']
    possible_responses = [
        "did you see the black panther film that was recently in theaters?",
        "what kind of genre do you prefer in books?",
        "are you a fan of standup comedy?",
        "are you a dog or a cat person?",
        "how are you doing today?",
        "do you like opera?",
        "how do you do?",
        "do you enjoy movies?",
        "do you like poetry?",
        "do you use netflix?"
    ]
    for sent in sentences:
        data = {"sentences_batch": [[sent]]}
        response = requests.post(url, json=data).json()[0][0]
        assert response.lower() in possible_responses, print(sent, '.', response)


if __name__ == '__main__':
    main_test()
