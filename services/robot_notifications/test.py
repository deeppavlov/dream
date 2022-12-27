import requests


def main():
    url = "http://0.0.0.0:8136/check"

    request_data = {
        "dialogs": [
            {"dialog_ids": "test_dialog_id", "human": {"attributes": {"performing_command": "move_forward_10"}}},
            {"dialog_ids": "test_dialog_id", "human": {"attributes": {"performing_command": "move_backward_10"}}},
        ]
    }

    result = requests.post(url, json=request_data).json()
    print(result)
    gold_result = [{"human_attributes": {}}, {"human_attributes": {"performing_command": None,
                                                  "performed_commands": ["move_forward_10"]}}]

    assert result == gold_result, f"Got\n{result}\n, but expected:\n{gold_result}"
    print("Success")


if __name__ == "__main__":
    main()
