import requests


def main():
    url = "http://0.0.0.0:8137"

    request_datas = [
        {
            "command": "move_backward_10",
            "dialog_ids": "test_dialog_id"
        },
        {
            "command": "move_forward_10",
            "dialog_ids": "test_dialog_id"
        }
    ]
    gold_results = [
        {'result': True},
        {'result': False},
        {'result': True},
        {'result': False},
        {'result': True},
        {'result': False}
    ]
    i = 0
    for endpoint in ["is_command_valid", "perform_command", "is_command_performed"]:
        for request_data in request_datas:
            result = requests.post(f"{url}/{endpoint}", json=request_data).json()
            assert result == gold_results[i]
            i += 1
    print("Success!")


if __name__ == "__main__":
    main()
