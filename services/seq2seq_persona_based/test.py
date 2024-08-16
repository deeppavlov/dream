import requests
import time


def test_respond():
    url = "http://0.0.0.0:8140/respond"

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
    gold = ['i am not sure. i am a vegetarian.']
    start_time = time.time()
    result = requests.post(url, json=test_data).json()
    total_time = time.time() - start_time
    print(f"Execution Time: {total_time} s")
    assert len(result[0][0]) > 0, print(f"Expected: {gold} but got: {result}")
    print(result[0][0], len(result[0][0]))
    assert total_time < 0.4, print(f"Expected: <={0.4}s but got: {result}s")
    print("Success")


if __name__ == "__main__":
    test_respond()
