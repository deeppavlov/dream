import requests


def main():
    url = "http://0.0.0.0:8136/check"

    request_data = {
        "dialogs": [
            {
                "human": {
                    "attributes": {
                        "performing_command": "move_forward_10"
                    }
                }
            }
        ]
    }

    result = requests.post(url, json=request_data).json()
    print(result)
    gold_result = [{"human_attributes": {}}]

    assert result == gold_result, f"Got\n{result}\n, but expected:\n{gold_result}"
    print("Success")


if __name__ == "__main__":
    main()
