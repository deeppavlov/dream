import requests


def main():
    url = "http://0.0.0.0:8114/respond"

    result = requests.post(
        url,
        json={
            "dialogs": [
                {
                    "human_utterances": [{"text": "i like my grandma", "annotations": {}}],
                    "bot_utterances": [],
                    "utterances": [{"text": "i like my grandma", "annotations": {}}],
                    "human": {"attributes": {}},
                },
                {
                    "human_utterances": [
                        {
                            "text": "fuck off",
                            "annotations": {
                                "blacklisted_words": {
                                    "profanity": True,
                                    "inappropriate": True,
                                    "restricted_topics": False,
                                }
                            },
                        }
                    ],
                    "bot_utterances": [],
                    "utterances": [
                        {
                            "text": "fuck off",
                            "annotations": {
                                "blacklisted_words": {
                                    "profanity": True,
                                    "inappropriate": True,
                                    "restricted_topics": False,
                                }
                            },
                        }
                    ],
                    "human": {"attributes": {}},
                },
            ]
        },
    ).json()
    gold_result = [{"human_attributes": {"age_group": "kid"}}, {"human_attributes": {"age_group": "adult"}}]
    assert result == gold_result, print(f"Got\n{result}\n, but expected:\n{gold_result}")

    print("Success")


if __name__ == "__main__":
    main()
