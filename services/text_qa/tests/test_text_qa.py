import os
import requests

import allure
import pytest


language = os.getenv("LANGUAGE", "EN")


@allure.description("""Test text-qa with questions in English""")
@pytest.mark.skipif(language == "RU", reason="no need to test russian questions")
@pytest.mark.parametrize(
    "request_data, gold_result",
    [
        (
            {
                "EN": {
                    "question_raw": ["Who was the first man in space?"],
                    "top_facts": [
                        [
                            "Yuri Gagarin was a Russian pilot and cosmonaut who became the first human to "
                            "journey into outer space."
                        ]
                    ],
                }
            },
            "Yuri Gagarin",
        ),
        (
            {
                "EN": {
                    "question_raw": ["Who played Sheldon Cooper in The Big Bang Theory?"],
                    "top_facts": [
                        [
                            "Sheldon Lee Cooper is a fictional character in the CBS television series "
                            "The Big Bang Theory and its spinoff series Young Sheldon, portrayed by actors "
                            "Jim Parsons in The Big Bang Theory."
                        ]
                    ],
                },
            },
            "Jim Parsons",
        ),
    ],
)
def test_text_qa(url: str, request_data, gold_result):
    result = requests.post(url, json=request_data[language]).json()
    print(result)
    res_ans = result[0][0]
    assert res_ans == gold_result


@allure.description("""Test text-qa with questions in Russian""")
@pytest.mark.skipif(language == "EN", reason="no need to test english questions")
@pytest.mark.parametrize(
    "request_data, gold_result",
    [
        (
            {
                "RU": {
                    "question_raw": ["Где живут кенгуру?"],
                    "top_facts": [["Кенгуру являются коренными обитателями Австралии."]],
                },
            },
            "Австралии",
        ),
        (
            {
                "RU": {
                    "question_raw": ["Кто придумал сверточную сеть?"],
                    "top_facts": [
                        [
                            "Свёрточная нейронная сеть - архитектура искусственных нейронных сетей, "
                            "предложенная Яном Лекуном в 1988 году."
                        ]
                    ],
                },
            },
            "Яном Лекуном",
        ),
    ],
)
def test_text_qa_ru(url: str, request_data, gold_result):
    result = requests.post(url, json=request_data[language]).json()
    res_ans = result[0][0]
    assert res_ans == gold_result
