import requests


URL = "http://0.0.0.0:8121/respond"

last_midas_labels = ["appreciation"]

gold = [{"appreciation": 0.09, "comment": 0.15, "opinion": 0.39, "pos_answer": 0.13, "statement": 0.25}]

if __name__ == "__main__":

    requested_data = {"last_midas_labels": last_midas_labels, "return_probas": 1}
    result = requests.post(URL, json=requested_data).json()
    assert result == gold

    requested_data = {"last_midas_labels": last_midas_labels, "return_probas": 0}
    result = requests.post(URL, json=requested_data).json()
    assert result[0] == "opinion"

    print("Success")
