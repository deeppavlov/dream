import requests

use_context = True


def main():
    url = "http://0.0.0.0:8113/respond"

    request_data = [
        {
            "utter_entities_batch": [
                [
                    [{"label": "gamename", "text": "mario"}],
                    [{"label": "videoname", "text": "interstellar"}],
                    [
                        {"label": "person", "text": "linus torvalds"},
                        {"label": "videoname", "text": "minecraft"},
                        {"label": "videoname", "text": "harry potter"},
                        {"label": "device", "text": "samsung"},
                    ],
                ]
            ]
        }
    ]

    gold_results = [['news_api_skill', 'dff_gossip_skill']]

    count = 0
    for data, gold_result in zip(request_data, gold_results):
        result = requests.post(url, json=data).json()[0]
        if result == gold_result:
            count += 1
        else:
            print(f"Got {result}, but expected: {gold_result}")

    assert count == len(request_data)
    print("Success")


if __name__ == "__main__":
    main()
