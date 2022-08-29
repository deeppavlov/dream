import requests


def main():
    url = "http://0.0.0.0:8078/model"

    request_data = [
        {
            "question_raw": ["Who was the first man in space?"],
            "top_facts": [
                [
                    "Yuri Gagarin was a Russian pilot and cosmonaut who became the first human to "
                    "journey into outer space."
                ]
            ],
        },
        {
            "question_raw": ["Who played Sheldon Cooper in The Big Bang Theory?"],
            "top_facts": [
                [
                    "Sheldon Lee Cooper is a fictional character in the CBS television series "
                    "The Big Bang Theory and its spinoff series Young Sheldon, portrayed by actors "
                    "Jim Parsons in The Big Bang Theory."
                ]
            ],
        },
    ]

    gold_results = [[["Yuri Gagarin", 0.7544615864753723, 0]], [["Jim Parsons", 0.9996281862258911, 151]]]
    count = 0
    for data, gold_result in zip(request_data, gold_results):
        result = requests.post(url, json=data).json()
        res_ans, res_conf = result[0][:2]
        gold_ans, gold_conf = gold_result[0][:2]
        if res_ans == gold_ans and round(res_conf, 2) == round(gold_conf, 2):
            count += 1
        else:
            print(f"Got {result}, but expected: {gold_result}")

    assert count == len(request_data)
    print("Success")


if __name__ == "__main__":
    main()
