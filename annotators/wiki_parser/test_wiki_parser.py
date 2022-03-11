import os
import requests


if os.getenv("LANGUAGE", "EN") == "RU":
    lang = "@ru"
else:
    lang = "@en"


def main():
    url = "http://0.0.0.0:8077/model"

    request_data_en = [
        {
            "parser_info": ["find_top_triplets"],
            "query": [[{"entity_substr": "Jurgen Schmidhuber", "entity_ids": ["Q92735"]}]],
        }
    ]
    request_data_ru = [
        {
            "parser_info": ["find_top_triplets"],
            "query": [[{"entity_substr": "Юрген Шмидхубер", "entity_ids": ["Q92735"]}]],
        }
    ]
    gold_results_en = [
        [
            {
                "animals_skill_entities_info": {},
                "entities_info": {
                    "Jurgen Schmidhuber": {
                        "age": 59,
                        "conf": 1.0,
                        "country of sitizenship": [["Q183", "Germany"]],
                        "date of birth": [['"+1963-01-17^^T"', "17 January 1963"]],
                        "entity_label": "Jürgen Schmidhuber",
                        "instance of": [["Q5", "human"]],
                        "occupation": [
                            ["Q15976092", "artificial intelligence researcher"],
                            ["Q1622272", "university teacher"],
                            ["Q82594", "computer scientist"],
                        ],
                        "plain_entity": "Q92735",
                        "pos": 0,
                        "token_conf": 1.0,
                        "types_2hop": [
                            ["Q82594", "computer scientist"],
                            ["Q14565186", "cognitive scientist"],
                            ["Q66666607", "academic profession"],
                            ["Q1622272", "university teacher"],
                            ["Q37226", "teacher"],
                            ["Q3400985", "academic"],
                            ["Q41835716", "faculty member"],
                            ["Q15976092", "artificial intelligence researcher"],
                            ["Q5", "human"],
                            ["Q28640", "profession"],
                            ["Q901", "scientist"],
                        ],
                    }
                },
                "topic_skill_entities_info": {},
                "utt_num": 0,
                "wiki_skill_entities_info": {},
            }
        ]
    ]
    gold_results_ru = [
        [
            {
                'animals_skill_entities_info': {},
                'entities_info': {
                    'Юрген Шмидхубер': {
                        'age': 59,
                        'conf': 1.0,
                        'country of sitizenship': [['Q183', 'Germany']],
                        'date of birth': [['"+1963-01-17^^T"', '17 January 1963']],
                        'entity_label': 'Jürgen Schmidhuber',
                        'instance of': [['Q5', 'human']],
                        'occupation': [
                            ['Q15976092', 'artificial intelligence researcher'],
                            ['Q1622272', 'university teacher'],
                            ['Q82594', 'computer scientist']
                        ],
                        'plain_entity': 'Q92735',
                        'pos': 0,
                        'token_conf': 1.0,
                        'types_2hop': [
                            ['Q41835716', 'faculty member'],
                            ['Q82594', 'computer scientist'],
                            ['Q28640', 'profession'],
                            ['Q901', 'scientist'],
                            ['Q3400985', 'academic'],
                            ['Q37226', 'teacher'],
                            ['Q15976092', 'artificial intelligence researcher'],
                            ['Q1622272', 'university teacher'],
                            ['Q5', 'human'],
                            ['Q66666607', 'academic profession'],
                            ['Q14565186', 'cognitive scientist']
                        ]
                    }
                },
                'topic_skill_entities_info': {},
                'utt_num': 0,
                'wiki_skill_entities_info': {}
            }
        ]
    ]

    count = 0
    if lang == "@ru":
        for data, gold_result in zip(request_data_ru, gold_results_ru):
            result = requests.post(url, json=data).json()
            if result == gold_result:
                count += 1
        else:
            print(f"Got {result}, but expected: {gold_result}")
        assert count == len(request_data_ru)
        if count == len(request_data_ru):
            print("Success")
    elif lang == "@en":
        for data, gold_result in zip(request_data_en, gold_results_en):
            result = requests.post(url, json=data).json()
            if result == gold_result:
                count += 1
        else:
            print(f"Got {result}, but expected: {gold_result}")
        assert count == len(request_data_en)
        if count == len(request_data_en):
            print("Success")


if __name__ == "__main__":
    main()
