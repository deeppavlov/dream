import requests
import time

from deeppavlov_kg import TerminusdbKnowledgeGraph

def main():
    start_time = time.time()
    BOT_KNOWLEDGE_MEMORIZER_PORT = 8044

    BOT_KNOWLEDGE_MEMORIZER_URL = f"http://0.0.0.0:{BOT_KNOWLEDGE_MEMORIZER_PORT}/respond"

    BOT_ID = "Bot/514b2c3d-bb73-4294-9486-04f9e099835e"
    request_data = {
            "utterances": [
                {
                    "text": "i have a dog and a cat",
                    "user": {"id": BOT_ID.split("/")[1]},
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
            ],
            "human_utterances": [
                {
                    "text": "What's your dog's name?",
                },
                {
                    "text": "",
                },
            ],
        }

    trials = 0
    response = None
    while response != 200:
        try:
            response = requests.post(BOT_KNOWLEDGE_MEMORIZER_URL, json=request_data).status_code

        except Exception as e:
            time.sleep(2)
            trials += 1
            if trials > 30:
                raise TimeoutError("Couldn't build the component")

    total_time = time.time() - start_time
    print("Success")
    print(f"bot knowledge memorizer launch time = {total_time:.3f}s")
    

if __name__ == "__main__":
    main()