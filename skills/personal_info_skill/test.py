import os
import requests


SKILL_URL = "http://0.0.0.0:8030/respond"
LANGUAGE = os.getenv("LANGUAGE", "EN")

if LANGUAGE == "RU":
    dialogs = {
        "dialogs": [
            {
                "utterances": [{"text": "меня зовут джо.", "annotations": {"ner": [[{"text": "Джо", "type": "PER"}]]}}],
                "bot_utterances": [],
                "human": {"attributes": {}, "profile": {"name": None}},
                "human_utterances": [
                    {"text": "Меня зовут джо.", "annotations": {"ner": [[{"text": "Джо", "type": "PER"}]]}}
                ],
            },
            {
                "utterances": [
                    {"text": "меня зовут не джо.", "annotations": {"ner": [[{"text": "Джо", "type": "PER"}]]}}
                ],
                "bot_utterances": [],
                "human": {"attributes": {}, "profile": {"name": None}},
                "human_utterances": [
                    {"text": "меня зовут не джо.", "annotations": {"ner": [[{"text": "Джо", "type": "PER"}]]}}
                ],
            },
            {
                "utterances": [
                    {"text": "я родом из москвы.", "annotations": {"ner": [[{"text": "москвы", "type": "LOC"}]]}}
                ],
                "bot_utterances": [],
                "human": {"attributes": {}, "profile": {"name": None}},
                "human_utterances": [
                    {"text": "я родом из москвы.", "annotations": {"ner": [[{"text": "москвы", "type": "LOC"}]]}}
                ],
            }
        ]
    }
    gold = [
        "Приятно познакомиться, Джо.",
        "Ой, извини. Как тебя зовут еще раз?",
        "А сейчас ты живешь в этом же месте?"
    ]
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
    gold = ["Nice to meet you, John."]

result = requests.post(SKILL_URL, json=dialogs, timeout=2)
result = result.json()

for i in range(len(dialogs['dialogs'])):
    print(f"check for human uttr `{dialogs['dialogs'][i]['human_utterances'][-1]['text']}`")
    assert result[i][0] == gold[i], print(result[i])

print("SUCCESS")
