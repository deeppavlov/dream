import requests


url = "http://0.0.0.0:8017/sentrewrite"
data = {
    "utterances_histories": [
        [["do you know lionel messi?"], ["yes, he is a football player."], ["who is the best, he or c.ronaldo?"]]
    ],
    "annotation_histories": [
        [
            {"ner": [[{"confidence": 1, "end_pos": 24, "start_pos": 13, "text": "lionel messi", "type": "PER"}]]},
            {"ner": [[]]},
            {"ner": [[{"confidence": 1, "end_pos": 32, "start_pos": 24, "text": "c.ronaldo", "type": "PER"}]]},
        ]
    ],
}

gold = [
    {
        "clusters": [
            [
                {
                    "end": 24,
                    "ner": {"offset": 1, "type": "PER"},
                    "resolved": "lionel messi",
                    "start": 12,
                    "text": "lionel messi",
                },
                {
                    "end": 33,
                    "ner": {"offset": 10000, "type": "O"},
                    "resolved": "lionel messi",
                    "start": 31,
                    "text": "he",
                },
                {
                    "end": 75,
                    "ner": {"offset": 10000, "type": "O"},
                    "resolved": "lionel messi",
                    "start": 73,
                    "text": "he",
                },
            ]
        ],
        "modified_sents": [
            "do you know lionel messi?",
            "yes, lionel messi is a football player.",
            "who is the best, lionel messi or c.ronaldo?",
        ],
    }
]
response = requests.post(url, json=data).json()
print(response)

assert response == gold, print(response)

print("SUCCESS!")
