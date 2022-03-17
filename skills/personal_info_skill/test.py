import os
import requests


SKILL_URL = "http://0.0.0.0:8030/respond"
LANGUAGE = os.getenv("LANGUAGE", "EN")

if LANGUAGE == "RU":
    dialogs = {
        "dialogs": [
            {
                "utterances": [{"text": "Меня зовут Джо", "annotations": {"ner": [[{"text": "Джо", "type": "PER"}]]}}],
                "bot_utterances": [],
                "human": {"attributes": {}, "profile": {"name": None}},
                "human_utterances": [
                    {"text": "Меня зовут Джо.", "annotations": {"ner": [[{"text": "Джо", "type": "PER"}]]}}
                ],
            }
        ]
    }
    gold = "Приятно познакомиться, Джо."
else:
    dialogs = {
        "dialogs": [
            {
                "utterances": [
                    {"text": "my name is john", "annotations": {"ner": [[{"text": "john", "type": "PER"}]]}}
                ],
                "bot_utterances": [],
                "human": {"attributes": {}, "profile": {"name": None}},
                "human_utterances": [
                    {"text": "my name is john", "annotations": {"ner": [[{"text": "john", "type": "PER"}]]}}
                ],
            }
        ]
    }
    gold = "Nice to meet you, John."

result = requests.post(SKILL_URL, json=dialogs, timeout=2)
result = result.json()

assert result[0][0] == gold, print(result)

print("SUCCESS")
