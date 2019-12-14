import requests
import json


def get_input_json(fname):
    with open(fname, "r") as f:
        res = json.load(f)
    return {"dialogs": res}


def main_test():
    url = 'http://0.0.0.0:8032/book_skill'
    input_data = get_input_json("test_configs/bug_user_utt.json")
    response = requests.post(url, json=input_data).json()[0]
    assert response == ['I agree. But there are some better books.', 0.98]
    print("SUCCESS BOOK SKILL TEST PASSED!")


if __name__ == '__main__':
    main_test()
