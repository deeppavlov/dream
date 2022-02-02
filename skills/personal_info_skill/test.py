import requests


SKILL_URL = "http://0.0.0.0:8030/respond"


dialogs = {
    "dialogs": [
        {
            "utterances": [{"text": "my name is john", "annotations": {"ner": [[{"text": "john", "type": "PER"}]]}}],
            "bot_utterances": [],
            "human": {"attributes": {}, "profile": {"name": None}},
            "human_utterances": [
                {"text": "my name is john", "annotations": {"ner": [[{"text": "john", "type": "PER"}]]}}
            ],
        }
    ]
}
gold = "Nice to meet you, john."
result = requests.post(SKILL_URL, json=dialogs, timeout=2)
result = result.json()

assert result[0][0] == "Nice to meet you, John.", print(result)

print("SUCCESS")
