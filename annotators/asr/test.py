import requests


def main():
    url = "http://0.0.0.0:8031/asr_check"
    input_data = {
        "speeches": [
            {
                "hypotheses": [
                    {"tokens": [{"confidence": 0.95, "value": "let's"}, {"confidence": 0.968, "value": "chat"}]}
                ]
            }
        ],
        "human_utterances": [[{"text": "let's chat"}]],
    }
    result = requests.post(url, json=input_data)
    print(result.json())
    assert result.json()[0]["asr_confidence"] == "high"

    input_data = {
        "speeches": [
            {"hypotheses": [{"tokens": [{"confidence": 0.6, "value": "let's"}, {"confidence": 0.6, "value": "chat"}]}]}
        ],
        "human_utterances": [[{"text": "let's chat"}]],
    }

    result = requests.post(url, json=input_data)
    assert result.json()[0]["asr_confidence"] == "medium"

    input_data = {
        "speeches": [
            {"hypotheses": [{"tokens": [{"confidence": 0.1, "value": "let's"}, {"confidence": 0.1, "value": "chat"}]}]}
        ],
        "human_utterances": [[{"text": "let's chat"}]],
    }
    result = requests.post(url, json=input_data)
    assert result.json()[0]["asr_confidence"] == "very_low"

    result = requests.post(url, json={"speeches": [[]], "human_utterances": [[]]})
    assert result.json()[0]["asr_confidence"] == "undefined"

    empty_json = {"hypotheses": [{"tokens": []}]}
    result = requests.post(url, json={"speeches": [empty_json], "human_utterances": [[]]})
    assert result.json()[0]["asr_confidence"] == "undefined"


if __name__ == "__main__":
    main()
