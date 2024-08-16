import time
import os
import requests

if __name__ == "__main__":
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
    start_time = time.time()
    trials = 0
    response = 104
    while response != 200:
        try:
            response = requests.post(url, json=test_data).status_code
        except:
            print("response", response)
            trials += 1
            time.sleep(2)
            if trials > 600:
                raise TimeoutError("Couldn't build the component")

    total_time = time.time() - start_time
    print(f"Rebuild time: {total_time}")
