import requests
import json


def get_input_json(fname):
    with open(fname, "r") as f:
        res = json.load(f)
    return {"dialogs": [res]}


def test_one_step_responses():
    url = 'http://0.0.0.0:8085/respond'

    print("test annotations")
    input_data = get_input_json("test_configs/test_annotations.json")
    for t in range(10):
        response = requests.post(url, json=input_data).json()[0]
        if any([response[0][i] for i in range(len(response[0]))]):
            print(f"success in try {t}")
            break
        if t == 9:
            assert any([response[0][i] for i in range(len(response[0]))]), print(response)

    print("test no annotations")
    input_data = get_input_json("test_configs/test_no_annotations.json")
    response = requests.post(url, json=input_data).json()[0]
    assert response[0][0] == '', print(response)

    print("SUCCESS!")


if __name__ == '__main__':
    test_one_step_responses()
