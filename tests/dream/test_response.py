import requests
import time


if __name__ == "__main__":
    url = "http://0.0.0.0:4242"
    user_id = "test"

    trials = 0
    result = requests.post(url, json={"user_id": user_id, "payload": "/start"})
    while result.status_code != 200:
        result = requests.post(url, json={"user_id": user_id, "payload": "/start"}).json()
        time.sleep(2)
        trials += 1
        if trials > 30:
            raise TimeoutError("/start is not working!")

    trials = 0
    result = requests.post(url, json={"user_id": user_id, "payload": "hey", "ignore_deadline_timestamp": True})
    while result.status_code != 200 or result.json()["active_skill"] == "timeout":
        # TODO: add such checking in the deploy prod
        time.sleep(4)
        trials += 1
        if trials > 30:
            raise TimeoutError(f"hey is not working! Response: {result.json()}")
    print("Success warmup", result.json())
