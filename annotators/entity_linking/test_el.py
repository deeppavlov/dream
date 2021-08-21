import requests

use_context = True


def main():
    url = "http://0.0.0.0:8075/model"

    request_data = [
        {"entity_substr": [["Forrest Gump"]], "template": [""], "context": [["Who directed Forrest Gump?"]]},
        {
            "entity_substr": [["Robert Lewandowski"]],
            "template": [""],
            "context": [["What team Robert Lewandowski plays for?"]],
        },
    ]

    if use_context:
        gold_results = [
            ["Q134773", "Q3077690", "Q552213", "Q5365088"],
            ["Q151269", "Q187312", "Q273773", "Q104913", "Q1153256"],
        ]

    else:
        gold_results = [
            ["Q134773", "Q3077690", "Q552213", "Q5365088", "Q17006552"],
            ["Q151269", "Q104913", "Q768144", "Q2403374", "Q170095"],
        ]
    count = 0
    for data, gold_result in zip(request_data, gold_results):
        result = requests.post(url, json=data).json()
        entity_ids = result[0][0]["entity_ids"]
        if entity_ids == gold_result:
            count += 1
        else:
            print(f"Got {result}, but expected: {gold_result}")

    assert count == len(request_data)
    print("Success")


if __name__ == "__main__":
    main()
