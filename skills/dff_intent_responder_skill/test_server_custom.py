import requests
import os
import json

# import common.test_utils as test_utils


INTENT_RESPONSE_PHRASES_FNAME = os.getenv("INTENT_RESPONSE_PHRASES_FNAME", "intent_response_phrases.json")
SERVICE_PORT = 8012
RANDOM_SEED = int(os.getenv("RANDOM_SEED", 2718))
URL = f"http://0.0.0.0:{SERVICE_PORT}/respond"

in_data = json.load(open("./custom_tests/intent_track_object.json"))

def handler(requested_data, random_seed):
    hypothesis = requests.post(URL, json={**requested_data, "random_seed": random_seed}).json()
    return hypothesis

def run_test(handler):
    hypothesis = handler(in_data, RANDOM_SEED)
    print(hypothesis)
  

# def run_test(handler):
#     print("Success")


if __name__ == "__main__":
    run_test(handler)

