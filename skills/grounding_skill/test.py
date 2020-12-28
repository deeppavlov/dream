import requests
import json


def get_input_json(fname):
    with open(fname, "r") as f:
        res = json.load(f)
    res['dialogs'][0]
    return res


def main_test():
    url = 'http://0.0.0.0:8080/grounding_skill'
    input_data = get_input_json("test_configs/test_dialog.json")
    response = requests.post(url, json=input_data).text
    response = response.replace('  ', ' ')
    topic_reply = 'about the following topics: Entertainment Movies, Movies TV'
    intent_reply = 'with the following intents: Information Delivery Intent'
    entity_reply = 'mentioned the following entities: star wars'
    assert topic_reply in response, response
    assert intent_reply in response, response
    assert entity_reply in response, response

if __name__ == '__main__':
    main_test()
