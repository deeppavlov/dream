import requests


def main_test():
    url = 'http://0.0.0.0:8008/api/rest/v1.0/ask'

    sent = "do you have a boyfriend"
    data = {"sentences_batch": [[sent]]}
    response = requests.post(url, json=data).json()[0][0]
    assert "I'm happily single. But if you know any nice guys, let me know!" in response, print(sent, '.', response)

    # misheard
    sentences = ["let's chat about"
                 ]
    possible_responses = [
        "I misheard you. what's it that you'd like to chat about?"
    ]
    for sent in sentences:
        data = {"sentences_batch": [[sent]]}
        response = requests.post(url, json=data).json()[0][0]
        assert response in possible_responses, print(sent, '.', response)

    # let's chat
    sentences = ["can you chat",
                 "can you chat with me",
                 "can we chat",
                 "can we chat now",
                 "let's have a conversation",
                 "do you want to have a conversation",
                 "do you wanna have a conversation",
                 "do you wanna chat",
                 "will you have a conversation with me",
                 "i want to talk to you",
                 "you wanna chat",
                 "would you like to have a conversation"
                 ]
    possible_responses = [
        "It is always a pleasure to talk with a good person. What do you want to talk about?",
        "Yeah, let's chat! What do you want to talk about?",
        "Let's chat. I like to talk so much! What do you want to talk about?"
    ]
    for sent in sentences:
        data = {"sentences_batch": [[sent]]}
        response = requests.post(url, json=data).json()[0][0]
        assert response in possible_responses, print(sent, '.', response)

    # what to talk about
    sentences = ["what do you wanna talk about",
                 "i do not know what do you wanna talk about",
                 "what would you like to talk about",
                 "so what do you wanna talk about",
                 "what else do you wanna talk about",
                 "whatever you wanna talk about",
                 "what do you wanna talk about now"
                 ]
    possible_responses = [
        "We can talk on different topics, like movies, books, or I can answer you questions.",
        "We can talk about movies. For example, what's the last movie you have seen?",
        "We can talk about books. Do you love reading?"
    ]
    for sent in sentences:
        data = {"sentences_batch": [[sent]]}
        response = requests.post(url, json=data).json()[0][0]
        assert response in possible_responses, print(sent, '.', response)

    # talk about something
    sentences = ["let's chat about ducks",
                 "can we chat about ducks",
                 "let's have a conversation about ducks"
                 "do you want to have a conversation about ducks"
                 ]
    possible_responses = ["You are first. Tell me something about",
                          "Yeah, let's talk about it!",
                          "Just tell me something I don't know about"
                          ]
    for sent in sentences:
        data = {"sentences_batch": [[sent]]}
        response = requests.post(url, json=data).json()[0][0]
        contains_possib_response = False
        for p_resp in possible_responses:
            if p_resp in response:
                contains_possib_response = True

        assert contains_possib_response is True, print(sent, '.', response)

    # talk about user
    sentences = ["let's chat about me",
                 "can we chat about me",
                 "let's have a conversation about me",
                 "do you want to have a conversation about me"
                 ]
    possible_responses = ["You are first. Tell me something about you.",
                          "Yeah, let's talk about you!",
                          "Just tell me something I don't know about you."
                          ]
    for sent in sentences:
        data = {"sentences_batch": [[sent]]}
        response = requests.post(url, json=data).json()[0][0]
        assert response in possible_responses, print(sent, '.', response)

    sentences = ['can you sing', 'can you sing me a song']
    for sent in sentences:
        data = {"sentences_batch": [[sent]]}
        response = requests.post(url, json=data).json()[0][0]
        assert "Daisy, Daisy" in response, print(sent, '.', response)

    sentences = ["let's chat about you",
                 "can we chat about you",
                 "let's have a conversation about you",
                 "do you want to have a conversation about you",
                 "let's talk about you",
                 'tell me about yourself']
    for sent in sentences:
        data = {"sentences_batch": [[sent]]}
        response = requests.post(url, json=data).json()[0][0]
        assert any([j in response for j in ['humans differ from socialbots',
                                            'strawberry ice cream',
                                            'different from my developers',
                                            'Those neural networks',
                                            'incognito here',
                                            'woman should be a mystery',
                                            'be a mysterious stranger',
                                            'The DNA of who'
                                            ]]), print(sent, '.', response)

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

    sentences = ["play sade geronemo", 'alexa play set your nemo', "alexa set a timer to morning"]

    for sent in sentences:
        data = {"sentences_batch": [[sent]]}
        response = requests.post(url, json=data).json()[0][0]
        assert "Alexa, stop, and try again" in response, print(sent, '.', response)


if __name__ == '__main__':
    main_test()
