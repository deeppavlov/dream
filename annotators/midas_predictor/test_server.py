import requests


URL = "http://0.0.0.0:8121/respond"

last_midas_labels = ["appreciation"]

gold = [
    {
        "appreciation": 0.08635394456289978,
        "comment": 0.14712153518123666,
        "opinion": 0.39445628997867804,
        "pos_answer": 0.1257995735607676,
        "statement": 0.2462686567164179,
    }
]


if __name__ == "__main__":
    requested_data = {"last_midas_labels": last_midas_labels, "return_probas": 1}
    result = requests.post(URL, json=requested_data).json()
    assert result == gold

    requested_data = {"last_midas_labels": last_midas_labels, "return_probas": 0}
    result = requests.post(URL, json=requested_data).json()
    assert isinstance(result[0], str) and result[0] in gold[0].keys()

    print("Success")
