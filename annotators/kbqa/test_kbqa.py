import allure
import pytest
import requests


@allure.description("""Test kbqa""")
@pytest.mark.parametrize(
    "request_data", "gold_answers",
    [
        {"x_init": ["Who is Donald Trump?"], "entities": [["Donald Trump"]], "entity_tags": [[["per", 1.0]]]},
        {"x_init": ["How old is Donald Trump?"], "entities": [["Donald Trump"]], "entity_tags": [[["per", 1.0]]]},
    ],
    ["Donald Trump is 45th president of the United States (2017–2021).", "Donald Trump is 77 years old."]
)
def test_kbqa(url: str, request_data: list[dict], gold_answers: list):
    count = 0
    for data, gold_ans in zip(request_data, gold_answers):
        result = requests.post(url, json=data).json()
        res_ans = result[0]["answer"]
        if res_ans == gold_ans:
            count += 1
        else:
            print(f"Got {res_ans}, but expected: {gold_ans}")
    assert count == len(request_data)
