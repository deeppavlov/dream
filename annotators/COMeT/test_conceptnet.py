import requests


def test_conceptnet():
    url = "http://0.0.0.0:8065/comet"

    request_data = {"input": "basketball", "category": ["SymbolOf", "HasProperty", "Causes", "CausesDesire"]}

    result = requests.post(url, json=request_data).json()

    gold_result = {
        "SymbolOf": {"e1": "basketball", "relation": "SymbolOf", "beams": ["basketball", "graduation", "football"]},
        "HasProperty": {"e1": "basketball", "relation": "HasProperty", "beams": ["spherical", "fun", "round"]},
        "Causes": {"e1": "basketball", "relation": "Causes", "beams": ["injury", "you feel tire", "you feel good"]},
        "CausesDesire": {"e1": "basketball", "relation": "CausesDesire", "beams": ["run marathon", "run", "jump"]},
    }

    assert result == gold_result, f"Got\n{result}\n, but expected:\n{gold_result}"
    print("Success")


def test_conceptnet_annotator():
    url = "http://0.0.0.0:8065/comet_annotator"

    request_data = {"nounphrases": [["basketball", "unicorn"], ["pancakes"], ["ieaundy karianne rania tecca dot"]]}

    result = requests.post(url, json=request_data).json()

    gold_result = [
        {
            "basketball": {
                "Causes": ["injury", "you feel tire", "you feel good"],
                "CausesDesire": ["run marathon", "run", "jump"],
                "HasProperty": ["spherical", "fun", "round"],
                "SymbolOf": ["basketball", "graduation", "football"],
            },
            "unicorn": {
                "Causes": ["good luck", "unicorn", "wisdom"],
                "CausesDesire": ["ride on unicorn", "ride horse", "ride on horse"],
                "HasProperty": ["rare", "beautiful", "very rare"],
                "SymbolOf": ["peace", "purity", "christianity"],
            },
        },
        {
            "pancakes": {
                "Causes": ["food to be eat", "breakfast", "food to eat"],
                "CausesDesire": ["have breakfast", "eat breakfast", "make breakfast"],
                "HasProperty": ["delicious", "tasty", "good"],
                "SymbolOf": ["breakfast", "food", "coffee"],
            }
        },
        {"ieaundy karianne rania tecca dot": {"Causes": [], "CausesDesire": [], "HasProperty": [], "SymbolOf": []}},
    ]

    assert result == gold_result, f"Got\n{result}\n, but expected:\n{gold_result}"
    print("Success")


if __name__ == "__main__":
    for test in [test_conceptnet, test_conceptnet_annotator]:
        test()
