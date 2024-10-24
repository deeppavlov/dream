import requests


if __name__ == "__main__":
    url = "http://0.0.0.0:4242"
    user_id = "test"

    trials = 0
    print("Input user utterance: my favorite place is venice")
    expected_output = "What are the odds? I also love venice. What impressed you the most there?"
    print(f"Expected bot utterance: {expected_output}")
    result = None
    while result != expected_output:
        response = requests.post(
            url, json={"user_id": user_id, "payload": "my favorite place is venice", "ignore_deadline_timestamp": True}
        ).json()
        result = response.get("response")
        # print(result)
        if result == expected_output:
            print(f"Success for node switch based on entity\nOutput bot utterance: {result}")
        trials += 1
        if trials > 10:
            print("Expected output doesn't match the result", result)
            break
