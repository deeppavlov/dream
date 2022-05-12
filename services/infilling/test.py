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

    text = ["Chris was bad at _.", "Chris was _ so he could not come."]

    request_data = {"text": text}

    result = requests.post(url, json=request_data).json()

    digits = 2
    result = round_struct(result, digits)
    print(result)
    assert result['predicted_tokens'][0].startswith('Chris was bad at'), f"Got\n{result}\n, but had to be starting with 'Chris was bad at math'"
    assert result['predicted_tokens'][1].startswith('Chris was') and result['predicted_tokens'][1].endswith('so he could not come.')
    print("Success")


if __name__ == "__main__":
    test_respond()
