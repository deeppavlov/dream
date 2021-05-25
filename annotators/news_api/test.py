import json
import requests

NEWS_API_ANNOTATOR_URL = "http://0.0.0.0:8112/respond"

request_data = json.load(open("test_input.json"))  # list of one dialog

result = requests.post(NEWS_API_ANNOTATOR_URL, json={"dialogs": request_data}).json()
assert len(result[0]) == 2, print(result)
assert result[0][0]["entity"] == "all", print(result)
assert result[0][1]["entity"] == "michael jordan", print(result)

print("SUCCESS")
