import requests


def main():
    url = "http://0.0.0.0:8078/model"

    request_data = [
        {
            "question_raw": ["Где живут кенгуру?"],
            "top_facts": [["Кенгуру являются коренными обитателями Австралии."]],
        },
        {
            "question_raw": ["Кто придумал сверточную сеть?"],
            "top_facts": [
                [
                    "Свёрточная нейронная сеть - архитектура искусственных нейронных сетей, предложенная Яном Лекуном"
                    " в 1988 году."
                ]
            ],
        },
    ]

    gold_results = ["Австралии", "Яном Лекуном"]
    count = 0
    for data, gold_ans in zip(request_data, gold_results):
        result = requests.post(url, json=data).json()
        res_ans = result[0][0]
        if res_ans == gold_ans:
            count += 1
        else:
            print(f"Got {result}, but expected: {gold_ans}")

    assert count == len(request_data)
    print("Success")


if __name__ == "__main__":
    main()
