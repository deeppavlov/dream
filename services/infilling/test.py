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
    url = "http://0.0.0.0:8122/respond"

    text = "Chris was bad at _."

    request_data = {"text": text}

    result = requests.post(url, json=request_data).json()

    gold_result = {'predicted_tokens' : 'Chris was bad at Math.' }
    digits = 2
    result = round_struct(result, digits)
    gold_result = round_struct(gold_result, digits)
    assert result['predicted_tokens'].startswith('Chris was bad at'), f"Got\n{result}\n, but expected:\n{gold_result}"
    print("Success")


if __name__ == "__main__":
    test_respond()
