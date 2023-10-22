import allure
import pytest
import requests


@allure.description("""Test fact retrieval""")
@pytest.mark.parametrize(
    "request_data, gold_results",
    [
        (
            {
                "dialog_history": [["Какая столица России?"]],
                "entity_substr": [["россии"]],
                "entity_tags": [["loc"]],
                "entity_pages": [[["Россия"]]],
            },
            "Росси́я или Росси́йская Федера́ция (РФ), — государство в Восточной Европе"
            " и Северной Азии. Территория России"
            " в её конституционных границах составляет км²; население страны (в пределах её заявленной территории) "
            "составляет чел. (). Занимает первое место в мире по территории, шестое — по объёму ВВП по ППС, и девятое "
            "— по численности населения. Столица — Москва. Государственный язык — русский. Денежная единица — "
            "российский рубль.",
        )
    ],
)
def test_fact_retrieval_rus(url: str, request_data: dict, gold_results: str):
    response = requests.post(url, json=request_data)
    result = response.json()
    assert response.status_code == 200
    assert result[0] and result[0][0] and result[0][0][0] == gold_results
