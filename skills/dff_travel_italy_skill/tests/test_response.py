import requests
import time
import json


if __name__ == "__main__":
    url = "http://0.0.0.0:4242"
    user_id = "test"

    trials = 0
    expected_output = 'What are the odds? I also love venice. What impressed you the most there?'
    result = None
    while result != expected_output:
        response = requests.post(url, json={"user_id": user_id, "payload": "my favorite place is venice", "ignore_deadline_timestamp": True}).json()
        result = response.get('response')
        # print(result)
        if result == expected_output:
            print("Success for node switch based on entity", result)
        trials += 1
        if trials > 10:
            print("Expected output doesn't match the result", result)
            break
