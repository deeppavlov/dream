import requests


def main():
    url = 'http://0.0.0.0:8065/comet'

    request_data = {"input": "go on a hike", "category": "MotivatedByGoal"}

    result = requests.post(url, json=request_data).json()

    gold_result = {
        "MotivatedByGoal": {
            "beams": [
                "exercise",
                "it be fun",
                "you like hike",
                "you enjoy hike",
                "explore"
            ],
            "relation": "MotivatedByGoal",
            "e1": "go on a hike"
        }
    }

    assert result == gold_result, f'Got\n{result}\n, but expected:\n{gold_result}'


if __name__ == '__main__':
    main()
