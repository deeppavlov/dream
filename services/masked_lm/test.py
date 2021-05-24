import requests


def round_struct(struct, digits):
    if isinstance(struct, dict):
        return {k: round_struct(v, digits) for k, v in struct.items()}
    elif isinstance(struct, list):
        return [round_struct(v, digits) for v in struct]
    elif isinstance(struct, float):
        return round(struct, digits)
    else:
        return struct


def test_respond():
    url = "http://0.0.0.0:8088/respond"

    text = ["Hello, it's [MASK] dog from my [MASK]."]

    request_data = {"text": text}

    result = requests.post(url, json=request_data).json()

    gold_result = {
        "predicted_tokens": [
            [
                {
                    "a": 0.21459759771823883,
                    "another": 0.0011624041944742203,
                    "his": 0.0008239049348048866,
                    "my": 0.05392618849873543,
                    "our": 0.0016213968629017472,
                    "some": 0.0008065433939918876,
                    "that": 0.014674700796604156,
                    "the": 0.6869651079177856,
                    "this": 0.002329436829313636,
                    "your": 0.015044458210468292,
                },
                {
                    "apartment": 0.03887254372239113,
                    "childhood": 0.015000063925981522,
                    "class": 0.01927136816084385,
                    "dream": 0.036867350339889526,
                    "dreams": 0.04079044237732887,
                    "house": 0.10746614634990692,
                    "neighborhood": 0.03330889344215393,
                    "office": 0.03672104701399803,
                    "room": 0.042806293815374374,
                    "world": 0.015730833634734154,
                },
            ]
        ]
    }
    digits = 2
    result = round_struct(result, digits)
    gold_result = round_struct(gold_result, digits)
    assert result == gold_result, f"Got\n{result}\n, but expected:\n{gold_result}"
    print("Success")


if __name__ == "__main__":
    test_respond()
