import requests


def main():
    url = "http://0.0.0.0:8042/send"

    request_data = {
        "last_human_utterances": [
            {
                "hypotheses": [
                    {
                        "skill_name": "dff_mint_skill",
                        "command_to_perform": "move_forward_10",
                    }
                ],
            },
            {
                "hypotheses": [
                    {
                        "skill_name": "dff_mint_skill",
                        "command_to_perform": "move_backward_10",
                    }
                ],
            },
        ],
        "bot_utterances": [
            {"active_skill": "dff_mint_skill"},
            {"active_skill": "dff_mint_skill"},
        ],
        "dialog_ids": ["test_dialog_id", "test_dialog_id"],
    }

    result = requests.post(url, json=request_data).json()
    print(result)
    gold_result = [{"human_attributes": {}}, {"human_attributes": {"performing_command": "move_backward_10"}}]

    assert result == gold_result, f"Got\n{result}\n, but expected:\n{gold_result}"
    print("Success")


if __name__ == "__main__":
    main()
