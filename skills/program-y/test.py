import difflib
import requests


def to_dialogs(sentences):
    utters = [{"text": sent, "user": {"user_type": "human"}} for sent in ["hi"] + sentences]
    return {"dialogs": [{"utterances": utters, "bot_utterances": utters, "human_utterances": utters}]}


def main_test():
    url = "http://0.0.0.0:8008/api/rest/v1.0/ask"

    sent = "do you have a boyfriend"
    data = to_dialogs([sent])
    response = requests.post(url, json=data).json()[0][0]
    assert "I'm happily single. But if you know any nice guys, let me know!" in response, print(sent, ".", response)

    # misheard
    sentences = ["let's chat about"]
    possible_responses = ["I misheard you. WHAT'S it that you'd like to chat about?"]
    for sent in sentences:
        data = to_dialogs([sent])
        response = requests.post(url, json=data).json()[0][0]
        possible_responses = [res.lower().strip() for res in possible_responses]
        response = response.lower().strip()
        assert_flag = [
            None
            for tgt_resp in possible_responses
            if difflib.SequenceMatcher(None, tgt_resp.split(), response.split()).ratio() > 0.9
        ]
        assert assert_flag, print(f"User: {sent}. Response: {response}")

    # let's chat
    sentences = [
        "can you chat",
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
        "would you like to have a conversation",
    ]
    possible_responses = [
        "It is always a pleasure to talk with a kind person. What do you want to talk about?",
        "It is always a pleasure to talk with a nice person. What do you want to talk about?",
        "Yeah, let's chat! What do you want to talk about?",
        "Let's chat. I love talking! What do you want to talk about?",
        "Hi, this is an Alexa Prize Socialbot! Yeah, let’s have a chat! What shall we talk about?",
        "Hi there, this is an Alexa Prize Socialbot! Lovely to meet you! What do you want to talk about?",
        "Hi there, this is an Alexa Prize Socialbot! Nice to meet you! What do you want to talk about?",
    ]
    for sent in sentences:
        data = to_dialogs([sent])
        response = requests.post(url, json=data).json()[0][0]
        possible_responses = [res.lower().strip() for res in possible_responses]
        response = response.lower().strip()
        assert_flag = [
            None
            for tgt_resp in possible_responses
            if difflib.SequenceMatcher(None, tgt_resp.split(), response.split()).ratio() > 0.9
        ]
        assert assert_flag, f"User: {sent}. Response: {response}"

    # what to talk about
    # sentences = [
    #     "what do you wanna talk about",
    #     "what would you like to talk about",
    #     "so what do you wanna talk about",
    #     "what else do you wanna talk about",
    #     "whatever you wanna talk about",
    #     "what do you wanna talk about now",
    # ]
    # possible_responses = [
    #     "We can talk on different topics, like movies, books, or I can answer you questions.",
    #     "We can talk about movies. For example, what's the last movie you have seen?",
    #     "We can talk about books. Do you love reading?",
    # ]
    # for sent in sentences:
    #     data = {"sentences_batch": [[sent]]}
    #     response = requests.post(url, json=data).json()[0][0]
    #     possible_responses = [res.lower().strip() for res in possible_responses]
    #     response = response.lower().strip()
    #     assert_flag = [
    #         None
    #         for tgt_resp in possible_responses
    #         if difflib.SequenceMatcher(None, tgt_resp.split(), response.split()).ratio() > 0.9
    #     ]
    #     assert assert_flag, print(f"User: {sent}. Response: {response}")

    # do not want to talk about it
    sentences = ["i don't wanna talk about it", "i do not know what do you wanna talk about"]
    possible_responses = [
        "Okay. Then you pick up the topic.",
        "As you wish. Let's chat about something you want. Pick up the topic, my friend.",
        "Okay. So, it's your turn. Pick up the topic.",
        "Let's chat about something you want. What do you want to talk about?",
    ]
    for sent in sentences:
        data = to_dialogs([sent])
        response = requests.post(url, json=data).json()[0][0]
        possible_responses = [res.lower().strip() for res in possible_responses]
        response = response.lower().strip()
        assert_flag = [
            None
            for tgt_resp in possible_responses
            if difflib.SequenceMatcher(None, tgt_resp.split(), response.split()).ratio() > 0.9
        ]
        assert assert_flag, print(f"User: {sent}. Response: {response}")

    # talk about something
    # sentences = [
    #     "let's chat about ducks",
    #     "can we chat about ducks",
    #     "let's have a conversation about ducks" "do you want to have a conversation about ducks",
    # ]
    # possible_responses = [
    #     "You are first. Tell me something about",
    #     "Yeah, let's talk about it!",
    #     "Just tell me something I don't know about",
    # ]
    # for sent in sentences:
    #     data = {"sentences_batch": [[sent]]}
    #     response = requests.post(url, json=data).json()[0][0].lower().strip()
    #     contains_possib_response = False
    #     for p_resp in possible_responses:
    #         if p_resp.lower().strip() in response:
    #             contains_possib_response = True
    #
    #     assert contains_possib_response is True, print(f"User: {sent}. Response: {response}")

    # talk about user
    # sentences = [
    #     "let's chat about me",
    #     "can we chat about me",
    #     "let's have a conversation about me",
    #     "do you want to have a conversation about me",
    # ]
    # possible_responses = [
    #     "You are first. Tell me something about you.",
    #     "Yeah, let's talk about you!",
    #     "Just tell me something I don't know about you.",
    # ]
    # for sent in sentences:
    #     data = {"sentences_batch": [[sent]]}
    #     response = requests.post(url, json=data).json()[0][0]
    #     possible_responses = [res.lower().strip() for res in possible_responses]
    #     response = response.lower().strip()
    #     assert_flag = [
    #         None
    #         for tgt_resp in possible_responses
    #         if difflib.SequenceMatcher(None, tgt_resp.split(), response.split()).ratio() > 0.9
    #     ]
    #     assert assert_flag, print(f"User: {sent}. Response: {response}")

    sentences = ["can you sing", "can you sing me a song"]
    for sent in sentences:
        data = to_dialogs([sent])
        response = requests.post(url, json=data).json()[0][0]
        assert "Daisy, Daisy" in response, print(f"User: {sent}. Response: {response}")

    sentences = [
        "let's chat about you",
        "can we chat about you",
        "let's have a conversation about you",
        "do you want to have a conversation about you",
        "let's talk about you",
        "tell me about yourself",
    ]
    for sent in sentences:
        data = to_dialogs([sent])
        response = requests.post(url, json=data).json()[0][0].lower().strip()
        assert any(
            [
                j.lower().strip() in response
                for j in [
                    "humans are different to socialbots",
                    "strawberry ice cream",
                    "different to my developers",
                    "Those neural networks",
                    "incognito here",
                    "woman should be a mystery",
                    "be a mysterious stranger",
                    "The DNA of who",
                ]
            ]
        ), print(f"User: {sent}. Response: {response}")

    sentences = ["can i ask you a question", "i have a question for you", "i have a question"]
    for sent in sentences:
        data = to_dialogs([sent])
        response = requests.post(url, json=data).json()[0][0].lower().strip()
        assert "You can ask me anything".lower().strip() in response, print(f"User: {sent}. Response: {response}")

    sentences = ["ask me a question", "do you wanna ask me a question"]
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
        "do you use netflix?",
    ]
    for sent in sentences:
        data = to_dialogs([sent])
        response = requests.post(url, json=data).json()[0][0].lower().strip()
        assert response in possible_responses, print(f"User: {sent}. Response: {response}")

    sentences = ["play sade geronemo", "alexa play set your nemo", "alexa set a timer to morning"]

    for sent in sentences:
        data = to_dialogs([sent])
        response = requests.post(url, json=data).json()[0][0]
        assert "stop" in response.lower().strip() or "social mode" in response.lower().strip(), print(
            f"User: {sent}. Response: {response}"
        )
    print("Success")


if __name__ == "__main__":
    main_test()
