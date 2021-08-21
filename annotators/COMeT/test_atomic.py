import requests


def main():
    url = "http://0.0.0.0:8053/comet"

    request_data = {
        "input": "PersonX went to a mall",
        "category": ["xReact", "xNeed", "xAttr", "xWant", "oEffect", "xIntent", "oReact"],
    }

    result = requests.post(url, json=request_data).json()

    gold_result = {
        "oEffect": {
            "beams": ["they go to the store", "they go to the mall"],
            "effect_type": "oEffect",
            "event": "PersonX went to a mall",
        },
        "oReact": {"beams": ["happy", "interested"], "effect_type": "oReact", "event": "PersonX went to a mall"},
        "xAttr": {
            "beams": ["curious", "fashionable", "interested"],
            "effect_type": "xAttr",
            "event": "PersonX went to a mall",
        },
        "xIntent": {
            "beams": ["to buy something", "to shop", "to buy things"],
            "effect_type": "xIntent",
            "event": "PersonX went to a mall",
        },
        "xNeed": {
            "beams": ["to drive to the mall", "to get in the car", "to drive to the mall"],
            "effect_type": "xNeed",
            "event": "PersonX went to a mall",
        },
        "xReact": {
            "beams": ["satisfied", "happy", "excited"],
            "effect_type": "xReact",
            "event": "PersonX went to a mall",
        },
        "xWant": {
            "beams": ["to buy something", "to go home", "to shop"],
            "effect_type": "xWant",
            "event": "PersonX went to a mall",
        },
    }

    assert result == gold_result, f"Got\n{result}\n, but expected:\n{gold_result}"
    print("Success")


if __name__ == "__main__":
    main()
