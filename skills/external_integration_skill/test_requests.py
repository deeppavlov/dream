import requests
ASSISTANT = "http://0.0.0.0:4242"

result = requests.post(
    ASSISTANT,
    json={
        "user_id": f"test-user-000",
        "payload": "Who are you? who built you? what can you do?",
    },
).json()
print(result)
