import requests


def main():
    url = "http://0.0.0.0:8004/batch_model"
    request_data = {
        "hypotheses": [
            "that a great name for a cat",
            "i don't want to talk about politics",
            "why did you call your cat this name?",
        ],
        "currentUtterance": "okay. i love cats. my cat is named putin.",
        "pastResponses": [" no. let's chat about animals. "],
        "pastUtterances": ["let's chat about jesus"],
    }
    gold_results = [
        {
            "isResponseComprehensible": 0.4768095314502716,
            "isResponseErroneous": 0.8192705512046814,
            "isResponseInteresting": 0.4681839048862457,
            "isResponseOnTopic": 0.14677414298057556,
            "responseEngagesUser": 0.7539744973182678,
        },
        {
            "isResponseComprehensible": 0.1574035882949829,
            "isResponseErroneous": 0.7897688150405884,
            "isResponseInteresting": 0.4750882089138031,
            "isResponseOnTopic": 0.013721293769776821,
            "responseEngagesUser": 0.14935889840126038,
        },
        {
            "isResponseComprehensible": 0.313213586807251,
            "isResponseErroneous": 0.7770318388938904,
            "isResponseInteresting": 0.5124449133872986,
            "isResponseOnTopic": 0.0315839946269989,
            "responseEngagesUser": 0.49631378054618835,
        },
    ]

    results = requests.post(url, json=request_data).json()[0]["batch"]
    print(results)
    for result, gold_result in zip(results, gold_results):
        for key in result.keys():
            difference = result[key] - gold_result[key]
        assert round(difference, 3) == 0, f"Got\n{result}\n, but expected:\n{gold_result}"
    print("Success")


if __name__ == "__main__":
    main()
