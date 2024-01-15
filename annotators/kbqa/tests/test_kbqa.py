import allure
import pytest
import requests


@allure.description("""Test kbqa""")
@pytest.mark.parametrize(
    "request_data, gold_answer",
    [
        (
            {"x_init": ["Who is Donald Trump?"], "entities": [["Donald Trump"]], "entity_tags": [[["per", 1.0]]]},
            "Donald Trump is 45th president of the United States (2017–2021).",
        ),
        (
            {"x_init": ["How old is Donald Trump?"], "entities": [["Donald Trump"]], "entity_tags": [[["per", 1.0]]]},
            "Donald Trump is 78 years old.",
        ),
    ],
)
def test_kbqa(url: str, request_data: dict, gold_answer: str):
    result = requests.post(url, json=request_data).json()
    res_ans = result[0]["answer"]
    assert res_ans == gold_answer
