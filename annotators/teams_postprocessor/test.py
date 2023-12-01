import requests


def test_skill():
    input_data = {
        "last_human_utterances": [
            {
                "text": "a list:onetwothat's it",
                "attributes": {
                    "teams_attachments": {
                        "content": "<p>a list:</p>\r\n<ul>\r\n<li>one</li><li>two</li></ul>\r\n<p>that's it</p>"
                    }
                },
            },
            {"text": "Help", "attributes": {"teams_attachments": {"content": "<p><span>Help&nbsp;</span></p>"}}},
        ],
        "pipelines": [["skills.dummy_skill"], ["skills.dummy_skill"]],
    }
    result = requests.post("http://0.0.0.0:8019/respond", json=input_data).json()
    gold_result = ["a list:\n— one\n— two\nthat's it", "/help"]
    assert result == gold_result, f"Got: {result} but expected: {gold_result}"
    print("SUCCESS!")


if __name__ == "__main__":
    test_skill()
