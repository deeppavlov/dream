import requests

URL = f"http://127.0.0.1:8050/"

# test_config = {"sentences": ['I eat apple', 'I like to swim']}

# ans = requests.post(URL, json=test_config)
ans = requests.get(URL)

print(ans.content)