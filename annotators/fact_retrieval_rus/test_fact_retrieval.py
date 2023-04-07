import requests


def main():
    url = "http://0.0.0.0:8130/model"

    request_data = [
        {
            "dialog_history": [["Какая столица России?"]],
            "entity_substr": [["россии"]],
            "entity_tags": [["loc"]],
            "entity_pages": [[["Россия"]]],
        }
    ]

    gold_results = [
        "Росси́я или Росси́йская Федера́ция (РФ), — государство в Восточной Европе и Северной Азии. Территория России"
        " в её конституционных границах составляет км²; население страны (в пределах её заявленной территории) "
        "составляет чел. (). Занимает первое место в мире по территории, шестое — по объёму ВВП по ППС, и девятое "
        "— по численности населения. Столица — Москва. Государственный язык — русский. Денежная единица — "
        "российский рубль."
    ]

    count = 0
    for data, gold_result in zip(request_data, gold_results):
        result = requests.post(url, json=data).json()
        if result[0] and result[0][0] and result[0][0][0] == gold_result:
            count += 1
        else:
            print(f"Got {result}, but expected: {gold_result}")

    assert count == len(request_data)
    print("Success")


if __name__ == "__main__":
    main()
