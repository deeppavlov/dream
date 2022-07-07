import json
import os
import requests


SKILL_URL = "http://0.0.0.0:8030/respond"
LANGUAGE = os.getenv("LANGUAGE", "EN")

with open(f"test_{LANGUAGE}.json", "r") as f:
    dialogs = json.load(f)

gold = []
for dialog in dialogs["dialogs"]:
    gold += [dialog.pop("expected_response")]

result = requests.post(SKILL_URL, json=dialogs, timeout=2)
result = result.json()

for i in range(len(dialogs["dialogs"])):
    print(f"check for uttr `{dialogs['dialogs'][i]['human_utterances'][-1]['text']}`\tgold response: `{gold[i]}`")
    assert result[i][0] == gold[i], print(result[i])

print("SUCCESS")
