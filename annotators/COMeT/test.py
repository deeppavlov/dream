import requests


def main():
    url = 'http://0.0.0.0:8053/comet'

    request_data = {"input_event": "PersonX went to a mall", "category": "xWant"}

    result = requests.post(url, json=request_data).json()

    gold_result = {
        "xWant": {
            "beams": [
                "to buy something",
                "to go home",
                "to buy things",
                "to shop",
                "to go to the store"
            ],
            "effect_type": "xWant",
            "event": "PersonX went to a mall"
        }
    }

    assert result == gold_result, f'Got\n{result}\n, but expected:\n{gold_result}'


if __name__ == '__main__':
    main()
