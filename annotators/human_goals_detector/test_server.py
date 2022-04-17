import requests

test_config = [
        {"sentences": ["War makes me feel awful"]},
        {"sentences": ["We by Zamyatin is my favorite dystopian novel!"]},
        {"sentences": ["Could you tell me about Harry Potter?"]},
        {"sentences": ["I feel bad, tell me about Harry Potter"]},
        {"sentences": ["I feel so good"]}
    ]

gold_result = [
    [
        ['share_personal_problems']
    ],
    [
        ['get_book_recommendation']
    ],
    [
        ['get_information_about_book', 'get_book_recommendation']
    ],
    [
        ['get_information_about_book', 'get_book_recommendation', 'share_personal_problems']
    ],
    [
        []
    ]
]

if __name__ == "__main__":
    url = "http://0.0.0.0:8122/respond"
    results = []
    count = 0
    for utt, gold_res in zip(test_config, gold_result):
        result = requests.post(url, json=utt).json()
        results.append(result)
        if result == gold_res:
            count += 1
        
    assert count == len(test_config)
    print("Success")
