import requests
import json
from copy import deepcopy
from utils import MIDAS_INTENT_ACKNOWLEDGMENETS


def get_input_json(fname):
    with open(fname, "r") as f:
        res = json.load(f)
    return res


def main_test():
    url = 'http://0.0.0.0:8080/grounding_skill'
    input_data = get_input_json("test_configs/test_dialog.json")
    response = requests.post(url, json=input_data)
    response = response.text.replace('  ', ' ')
    reply = "You just told me about star wars, right?"
    assert reply in response, response.json()

    # check acknowledgement
    new_input_data = deepcopy(input_data)
    new_input_data["dialogs"][0]["human_utterances"][-1]["text"] = "what do you think about horses"
    new_input_data["dialogs"][0]["human_utterances"][-1]["annotations"]["cobot_nounphrases"] = ["horses"]
    new_input_data["dialogs"][0]["human_utterances"][-1]["annotations"]["midas_classification"] = {
        "open_question_opinion": 1.0}
    response = requests.post(url, json=new_input_data)
    assert "horses" in response.text, response.json()

    new_input_data = deepcopy(input_data)
    new_input_data["dialogs"][0]["human_utterances"][-1]["text"] = "what are the horses"
    new_input_data["dialogs"][0]["human_utterances"][-1]["annotations"]["midas_classification"] = {
        "open_question_factual": 1.0}
    response = requests.post(url, json=new_input_data)
    assert "what are the horses" in response.text, response.json()

    new_input_data = deepcopy(input_data)
    new_input_data["dialogs"][0]["human_utterances"][-1]["text"] = "what is your horses name"
    new_input_data["dialogs"][0]["human_utterances"][-1]["annotations"]["midas_classification"] = {
        "open_question_personal": 1.0}
    response = requests.post(url, json=new_input_data)
    assert "what is my horses name" in response.text, response.json()

    new_input_data = deepcopy(input_data)
    new_input_data["dialogs"][0]["human_utterances"][-1]["text"] = "do you know about horses"
    new_input_data["dialogs"][0]["human_utterances"][-1]["annotations"]["midas_classification"] = {
        "yes_no_question": 1.0}
    response = requests.post(url, json=new_input_data)
    assert "whether I know about horses".lower() in response.text.lower(), response.json()

    new_input_data = deepcopy(input_data)
    new_input_data["dialogs"][0]["human_utterances"][-1]["text"] = "yes"
    new_input_data["dialogs"][0]["human_utterances"][-1]["annotations"]["midas_classification"] = {"pos_answer": 1.0}
    response = requests.post(url, json=new_input_data)
    assert any([resp in response.text for resp in MIDAS_INTENT_ACKNOWLEDGMENETS["pos_answer"]]), response.json()

    new_input_data = deepcopy(input_data)
    new_input_data["dialogs"][0]["human_utterances"][-1]["text"] = "no"
    new_input_data["dialogs"][0]["human_utterances"][-1]["annotations"]["midas_classification"] = {"neg_answer": 1.0}
    response = requests.post(url, json=new_input_data)
    assert any([resp in response.text for resp in MIDAS_INTENT_ACKNOWLEDGMENETS["neg_answer"]]), response.json()

    print("Success!")


if __name__ == '__main__':
    main_test()
