import requests


URL = 'http://0.0.0.0:4242'


def test_workflow_bug():
    response = requests.post(URL, json={"user_id": "test", "payload": "yes", "speech": {}}).json()
    assert "response" in response.keys()
    response = requests.post(URL, json={"user_id": "test", "payload": ""}).json()
    assert "response" in response.keys()
    response = requests.post(URL, json={"user_id": "test", "payload": "yes"}).json()
    assert "response" in response.keys()
    print("SUCCESS test workflow bug")


def test_asr_low_confidence():
    asr_responses = ["Excuse me, I misheard you. Could you repeat that, please?",
                     "I couldn't hear you. Could you say that again, please?",
                     "Sorry, I didn't catch that. Could you say it again, please?"
                     ]
    speech = {'hypotheses': [{'tokens': [{'confidence': 0.4, 'value': "yes"}]}]}
    response = requests.post(URL, json={"user_id": "test", "payload": "yes", "speech": speech}).json()
    assert response['response'] in asr_responses
    print("SUCCESS test_asr_low_confidence from agent")


def get_speech(user_sent, conf=0.6):
    speech_tokens = [{'confidence': conf, 'value': t} for t in user_sent.split(" ")]
    speech = {'hypotheses': [{'tokens': speech_tokens}]}
    return speech


def test_asr_medium_confidence():
    response = requests.post(URL, json={"user_id": "test", "payload": "/start"})
    response = requests.post(URL, json={"user_id": "test", "payload": "hi"})

    user_sent = "what is your favorite thing to eat?"
    responses = [f"Excuse me, I misheard you. Have you said: \"{user_sent}\"?"]
    response = requests.post(URL,
                             json={"user_id": "test", "payload": user_sent, "speech": get_speech(user_sent)}).json()
    assert response['response'] in responses, print(f"response {response['response']} not in {responses}")

    # Should not re ask if it has medium confidence twice
    user_sent = "yes"
    responses = [f"Excuse me, I misheard you. Have you said: \"{user_sent}\"?"]
    response = requests.post(URL,
                             json={"user_id": "test", "payload": user_sent, "speech": get_speech(user_sent)}).json()
    assert response['response'] not in responses and 'Have you said' not in response['response'], print(response)

    # Should return to yes no asr
    user_sent = "what is your favorite thing to eat?"
    responses = [f"Excuse me, I misheard you. Have you said: \"{user_sent}\"?"]
    response = requests.post(URL,
                             json={"user_id": "test", "payload": user_sent, "speech": get_speech(user_sent)}).json()
    assert response['response'] in responses, print(f"response {response['response']} not in {responses}", response)

    responses = ["What is it that you'd like to chat about?"]
    speech = {'hypotheses': [{'tokens': [{'confidence': 0.9, 'value': "no"}]}]}
    response = requests.post(URL, json={"user_id": "test", "payload": "no", "speech": speech}).json()
    assert response['response'] in responses, print(f"response {response['response']} not in {responses}")

    print("SUCCESS test_asr_medium_confidence from agent")


if __name__ == "__main__":
    test_workflow_bug()
    test_asr_low_confidence()
    # test_asr_medium_confidence()
