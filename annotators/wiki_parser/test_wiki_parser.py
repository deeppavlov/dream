import os

import allure
import pytest
import requests


if os.getenv("LANGUAGE", "EN") == "RU":
    lang = "@ru"
else:
    lang = "@en"


@allure.description("""Test parsing en wiki""")
@pytest.mark.parametrize(
    "request_data, gold_results",
    [
        (
            {
                "parser_info": ["find_top_triplets"],
                "query": [[{"entity_substr": "Jurgen Schmidhuber", "entity_ids": ["Q92735"]}]],
            },
            [
                {
                    "animals_skill_entities_info": {},
                    "entities_info": {
                        "Jurgen Schmidhuber": {
                            "age": 60,
                            "conf": 1.0,
                            "country of sitizenship": [["Q183", "Germany"]],
                            "date of birth": [['"+1963-01-17^^T"', "17 January 1963"]],
                            "entity_label": "Jürgen Schmidhuber",
                            "instance of": [["Q5", "human"]],
                            "occupation": [
                                ["Q15976092", "artificial intelligence researcher"],
                                ["Q1622272", "university teacher"],
                                ["Q1650915", "researcher"],
                                ["Q82594", "computer scientist"],
                            ],
                            "plain_entity": "Q92735",
                            "pos": 0,
                            "token_conf": 1.0,
                            "types_2hop": [
                                ["Q12737077", "occupation"],
                                ["Q14565186", "cognitive scientist"],
                                ["Q15976092", "artificial intelligence researcher"],
                                ["Q15980158", "non-fiction writer"],
                                ["Q1622272", "university teacher"],
                                ["Q1650915", "researcher"],
                                ["Q28640", "profession"],
                                ["Q3400985", "academic"],
                                ["Q37226", "teacher"],
                                ["Q4164871", "position"],
                                ["Q5", "human"],
                                ["Q5157565", "computer professional"],
                                ["Q5428874", "faculty member"],
                                ["Q66666607", "academic profession"],
                                ["Q66666685", "academic professional"],
                                ["Q82594", "computer scientist"],
                            ],
                        }
                    },
                    "topic_skill_entities_info": {},
                    "utt_num": 0,
                    "wiki_skill_entities_info": {},
                }
            ],
        )
    ],
)
@pytest.mark.skipif(lang="@ru")
def test_wiki_parser_en(url: str, request_data: dict, gold_results: list[dict]):
    response = requests.post(url, json=request_data)
    result = response.json()
    assert response.status_code == 200
    assert result == gold_results


@allure.description("""Test parsing ru wiki""")
@pytest.mark.parametrize(
    "request_data, gold_results",
    [
        (
            {
                "parser_info": ["find_top_triplets"],
                "query": [[{"entity_substr": "Юрген Шмидхубер", "entity_ids": ["Q92735"]}]],
            },
            [
                {
                    "animals_skill_entities_info": {},
                    "entities_info": {
                        "Юрген Шмидхубер": {
                            "age": 60,
                            "conf": 1.0,
                            "country of sitizenship": [["Q183", "Германия"]],
                            "date of birth": [['"+1963-01-17^^T"', "17 January 1963"]],
                            "entity_label": "Шмидхубер, Юрген",
                            "instance of": [["Q5", "человек"]],
                            "occupation": [
                                ["Q15976092", "исследователь искусственного интеллекта"],
                                ["Q1622272", "преподаватель университета"],
                                ["Q1650915", "исследователь"],
                                ["Q82594", "специалист в области информатики"],
                            ],
                            "plain_entity": "Q92735",
                            "pos": 0,
                            "token_conf": 1.0,
                            "types_2hop": [
                                ["Q12737077", "род занятий"],
                                ["Q15976092", "исследователь искусственного интеллекта"],
                                ["Q15980158", "писатель-документалист"],
                                ["Q1622272", "преподаватель университета"],
                                ["Q1650915", "исследователь"],
                                ["Q28640", "профессия"],
                                ["Q3400985", "научно-педагогический работник"],
                                ["Q37226", "учитель"],
                                ["Q4164871", "должность"],
                                ["Q5", "человек"],
                                ["Q5157565", "профессия в ИТ"],
                                ["Q5428874", "преподаватель"],
                                ["Q66666607", "академическая профессия"],
                                ["Q66666685", "академический профессионал"],
                                ["Q82594", "специалист в области информатики"],
                            ],
                        }
                    },
                    "topic_skill_entities_info": {},
                    "utt_num": 0,
                    "wiki_skill_entities_info": {},
                }
            ],
        )
    ],
)
@pytest.mark.skipif(lang="@en")
def test_wiki_parser_ru(url: str, request_data: dict, gold_results: list[dict]):
    response = requests.post(url, json=request_data)
    result = response.json()
    assert response.status_code == 200
    assert result == gold_results
