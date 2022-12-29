import requests


URL = "http://0.0.0.0:8129/respond"

res = requests.post(
    URL,
    json={"utterances":
           [{"text": "i have a dog",
             "user": {"id": "1234"},
             "annotations": {"property_extraction":
                              {"triplet": {"subject": "user", "relation": "have_pet", "object": "dog"}}}}]}
).json()

res = requests.post(
    URL,
    json={"utterances":
           [{"text": "i like dogs",
             "user": {"id": "1234"},
             "annotations": {"property_extraction":
                              {"triplet": {"subject": "user", "relation": "like_animal", "object": "dog"}}}}]}
).json()
