import requests


def main():
    url = "http://0.0.0.0:8136/check_notifications"

    request_data = {
        "annotated_bot_utterances": [
            {
                "text": "Moving forward for 10 meters",
                "confidence": 1.0,
                "attributes": {"robot_command": "move_forward_10"},
            }
        ]
    }

    result = requests.post(url, json=request_data).json()
    print(result)
    gold_result = ["Failed"]

    assert result == gold_result, f"Got\n{result}\n, but expected:\n{gold_result}"
    print("Success")


if __name__ == "__main__":
    main()
