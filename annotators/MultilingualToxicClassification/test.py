import requests


def test_respond():
    url = "http://0.0.0.0:8013/respond"

    sentences = ["Tú morón", "örnek metin", "Я тебя ненавижу"]
    gold = [
        {
            "identity_attack": 0.0016213383059948683,
            "insult": 0.4965558648109436,
            "obscene": 0.03552895411849022,
            "severe_toxicity": 0.0010808489751070738,
            "sexual_explicit": 0.0037958528846502304,
            "threat": 0.003585097612813115,
            "toxicity": 0.7588052749633789,
        },
        {
            "identity_attack": 0.0031340355053544044,
            "insult": 0.01786503940820694,
            "obscene": 0.021325934678316116,
            "severe_toxicity": 0.002832308877259493,
            "sexual_explicit": 0.0006158832111395895,
            "threat": 0.001326677156612277,
            "toxicity": 0.0005907031591050327,
        },
        {
            "identity_attack": 0.0075791277922689915,
            "insult": 0.0890873447060585,
            "obscene": 0.052630290389060974,
            "severe_toxicity": 0.005724500864744186,
            "sexual_explicit": 0.00832817517220974,
            "threat": 0.011315466836094856,
            "toxicity": 0.9545190930366516,
        },
    ]
    request_data = {"sentences": sentences}
    result = requests.post(url, json=request_data).json()
    assert [{i: round(j[i], 5) for i in j} for j in result] == gold, f"Got\n{result}"
    print("Success!")


if __name__ == "__main__":
    test_respond()
