import requests


def test_respond():
    url = "http://0.0.0.0:8131/respond"

    test_data = {
        "last_annotated_utterances": [
            {
                "text": "What should I cook for a dinner?",
                "annotations": {
                    "relative_persona_extractor": {
                        "persona": ["I like ice-cream.", "I hate onions."],
                        "max_similarity": 0.8,
                    },
                    "midas_classification": [{"open_question_personal": 1.0}],
                },
            }
        ],
        "utterances_histories": [
            [
                "What are you doing?",
                "I am planning what to cook.",
                "Sounds interesting.",
                "What should I cook for a dinner?",
            ]
        ],
    }
    gold = []

    result = requests.post(url, json=test_data).json()

    assert len(result[0][0]) > 0, print(f"Expected: {gold} but got: {result}")
    print("Success")


if __name__ == "__main__":
    test_respond()
