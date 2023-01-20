import os
import requests


language = os.getenv("LANGUAGE", "EN")


def main():
    url = "http://0.0.0.0:8078/model"

    request_data = {
        "RU": [
            {
                "question_raw": ["Где живут кенгуру?"],
                "top_facts": [["Кенгуру являются коренными обитателями Австралии."]],
            },
            {
                "question_raw": ["Кто придумал сверточную сеть?"],
                "top_facts": [
                    [
                        "Свёрточная нейронная сеть - архитектура искусственных нейронных сетей, "
                        "предложенная Яном Лекуном в 1988 году."
                    ]
                ],
            },
        ],
        "EN": [
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
        ],
    }
    gold_results = {"RU": ["Австралии", "Яном Лекуном"], "EN": ["Yuri Gagarin", "Jim Parsons"]}
    count = 0
    for data, gold_ans in zip(request_data[language], gold_results[language]):
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
