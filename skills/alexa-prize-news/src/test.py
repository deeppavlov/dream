import requests
import json


def get_input_json(fname):
    with open(fname, "r") as f:
        res = json.load(f)
    return {"dialogs": res}


def test_one_step_responses():
    url = "http://0.0.0.0:8027/respond"
    folder = "/src/src"

    print("tell_me_some_news")
    input_data = get_input_json(f"{folder}/test_configs/tell_me_some_news.json")
    response = requests.post(url, json=input_data).json()[0]
    assert "I could not find some specific news. So, here is one of the latest news from Washington Post" in response[0]
    assert response[1:] == [0.95, {"can_continue": "can", "mode": None}], print(response)
    #
    # print("tell_me_some_news_yes")
    # input_data = get_input_json(f"{folder}/test_configs/tell_me_some_news_yes.json")
    # response = requests.post(url, json=input_data).json()[0]
    # assert "The following news is from Washington Post:" in response[0], print(response)
    # assert response[1:] == [1.0, {'mode': "body"}], print(response)

    print("tell_me_news_about_trump")
    input_data = get_input_json(f"{folder}/test_configs/tell_me_news_about_trump.json")
    response = requests.post(url, json=input_data).json()[0]
    assert "Do you want to hear more?" in response[0]
    assert response[1:] == [0.98, {"can_continue": "can", "mode": "entity"}], print(response)

    print("tell_me_news_about_trump_yes")
    input_data = get_input_json(f"{folder}/test_configs/tell_me_news_about_trump_yes.json")
    response = requests.post(url, json=input_data).json()[0]
    assert "The following news is from Washington Post:" in response[0]
    assert response[1:] == [1.0, {"mode": "body"}], print(response)


print("SUCCESS!")


if __name__ == "__main__":
    test_one_step_responses()
