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


def test_asr():
    asr_responses = ["Excuse me, I misheard you. Could you repeat that, please?",
                     "I couldn't hear you. Could you say that again, please?",
                     "Sorry, I didn't catch that. Could you say it again, please?"
                     ]
    speech = {'hypotheses': [{'tokens': [{'confidence': 0.4, 'value': "yes"}]}]}
    response = requests.post(URL, json={"user_id": "test", "payload": "yes", "speech": speech}).json()
    assert response['response'] in asr_responses
    print("SUCCESS test asr from agent")


if __name__ == "__main__":
    test_workflow_bug()
    test_asr()
