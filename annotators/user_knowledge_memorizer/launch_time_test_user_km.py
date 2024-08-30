import requests
import time


def main():
    start_time = time.time()
    USER_KNOWLEDGE_MEMORIZER_PORT = 8027

    USER_KNOWLEDGE_MEMORIZER_URL = f"http://0.0.0.0:{USER_KNOWLEDGE_MEMORIZER_PORT}/respond"

    USER_ID = "User/b75d2700259bdc44sdsdf85e7f530ed"
    request_data = {
        "last_human_annotated_utterance": [
            {
                "text": "i have a dog and a cat",
                "user": {"id": USER_ID.split("/")[1]},
                "annotations": {
                    "property_extraction": [
                        {
                            "triplets": [
                                {"subject": "user", "relation": "HAVE PET", "object": "dog"},
                                {"subject": "user", "relation": "LIKE GOTO", "object": "park"},
                            ]
                        }
                    ],
                    "custom_entity_linking": [],
                },
            },
            {
                "text": "",
                "user": {"id": ""},
                "annotations": {
                    "property_extraction": [{}],
                    "custom_entity_linking": [],
                },
            },
        ]
    }

    trials = 0
    response = None
    while response != 200:
        try:
            response = requests.post(USER_KNOWLEDGE_MEMORIZER_URL, json=request_data).status_code

        except Exception:
            time.sleep(2)
            trials += 1
            if trials > 30:
                raise TimeoutError("Couldn't build the component")

    total_time = time.time() - start_time
    print("Success")
    print(f"user knowledge memorizer launch time = {total_time:.3f}s")


if __name__ == "__main__":
    main()
