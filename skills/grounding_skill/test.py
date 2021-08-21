import requests
import json
from copy import deepcopy


def get_input_json(fname):
    with open(fname, "r") as f:
        res = json.load(f)
    return res


def main_test():
    url = 'http://0.0.0.0:8080/grounding_skill'
    input_data = get_input_json("test_configs/test_dialog.json")
    with open("universal_intent_responses.json", "r") as f:
        UNIVERSAL_INTENT_RESPONSES = json.load(f)

    response = requests.post(url, json=input_data)
    reply = "You just told me about star wars, right?"
    assert reply in response.text.replace('  ', ' '), response.json()

    # check acknowledgement
    new_input_data = deepcopy(input_data)
    new_input_data["dialogs"][0]["human_utterances"][-1]["text"] = "what do you think about horses"
    new_input_data["dialogs"][0]["human_utterances"][-1]["annotations"]["sentseg"] = {
        "segments": [new_input_data["dialogs"][0]["human_utterances"][-1]["text"]]
    }
    new_input_data["dialogs"][0]["human_utterances"][-1]["annotations"]["entity_detection"] = {
        "entities": ["horses"],
        "labelled_entities": [{"text": "horses", "label": "misc"}]
    }
    new_input_data["dialogs"][0]["human_utterances"][-1]["annotations"]["midas_classification"] = [{
        "open_question_opinion": 1.0}]
    response = requests.post(url, json=new_input_data)
    assert "horses" in response.text, response.json()

    new_input_data = deepcopy(input_data)
    new_input_data["dialogs"][0]["human_utterances"][-1]["text"] = "what are the horses"
    new_input_data["dialogs"][0]["human_utterances"][-1]["annotations"]["sentseg"] = {
        "segments": [new_input_data["dialogs"][0]["human_utterances"][-1]["text"]]
    }
    new_input_data["dialogs"][0]["human_utterances"][-1]["annotations"]["entity_detection"] = {
        "entities": ["horses"],
        "labelled_entities": [{"text": "horses", "label": "misc"}]
    }
    new_input_data["dialogs"][0]["human_utterances"][-1]["annotations"]["midas_classification"] = [{
        "open_question_factual": 1.0}]
    response = requests.post(url, json=new_input_data)
    assert "what are the horses" in response.text, response.json()

    new_input_data = deepcopy(input_data)
    new_input_data["dialogs"][0]["human_utterances"][-1]["text"] = "what is your horses name"
    new_input_data["dialogs"][0]["human_utterances"][-1]["annotations"]["sentseg"] = {
        "segments": [new_input_data["dialogs"][0]["human_utterances"][-1]["text"]]
    }
    new_input_data["dialogs"][0]["human_utterances"][-1]["annotations"]["entity_detection"] = {
        "entities": ["horses name"],
        "labelled_entities": [{"text": "horses", "label": "misc"}]
    }
    new_input_data["dialogs"][0]["human_utterances"][-1]["annotations"]["midas_classification"] = [{
        "open_question_personal": 1.0}]
    response = requests.post(url, json=new_input_data)
    assert "what is my horses name" in response.text, response.json()

    new_input_data = deepcopy(input_data)
    new_input_data["dialogs"][0]["human_utterances"][-1]["text"] = "do you know about horses"
    new_input_data["dialogs"][0]["human_utterances"][-1]["annotations"]["sentseg"] = {
        "segments": [new_input_data["dialogs"][0]["human_utterances"][-1]["text"]]
    }
    new_input_data["dialogs"][0]["human_utterances"][-1]["annotations"]["entity_detection"] = {
        "entities": ["horses"],
        "labelled_entities": [{"text": "horses", "label": "misc"}]
    }
    new_input_data["dialogs"][0]["human_utterances"][-1]["annotations"]["midas_classification"] = [{
        "yes_no_question": 1.0}]
    response = requests.post(url, json=new_input_data)
    assert "whether I know about horses".lower() in response.text.lower(), response.json()

    # check universal intent responses
    new_input_data = deepcopy(input_data)
    new_input_data["dialogs"][0]["human_utterances"][-1]["annotations"]["midas_classification"] = [{"opinion": 1.0}]
    new_input_data["dialogs"][0]["human_utterances"][-1]["annotations"]["cobot_dialogact"] = {
        "intents": ["General_ChatIntent"], "topics": ["Other"]
    }
    response = requests.post(url, json=new_input_data)
    assert any([resp in response.text for resp in UNIVERSAL_INTENT_RESPONSES["opinion"]]), response.json()

    print("Success!")


if __name__ == '__main__':
    main_test()
