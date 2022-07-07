import requests


SKILL_URL = "http://0.0.0.0:8054/meta_script"

dialogs = {
    "dialogs": [
        {
            "utterances": [
                {
                    "text": "jessy played piano",
                    "annotations": {},
                }
            ],
            "bot_utterances": [],
            "human": {"attributes": {}},
            "human_utterances": [
                {
                    "text": "jessy played piano",
                    "annotations": {},
                }
            ],
        }
    ]
}

result = requests.post(SKILL_URL, json=dialogs, timeout=1.5)
result = result.json()
gold = "piano"
assert result[0][1][0] == 0.8 and gold in result[0][0][0], print(result)

print("SUCCESS")
