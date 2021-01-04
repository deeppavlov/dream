import requests


def main():
    url = 'http://0.0.0.0:8004/evaluate'

    request_data = {"currentUtterance": "okay. i love cats. my cat is named putin.",
                    "pastUtterances": ["let's chat about jesus"],
                    "pastResponses": ["no. let's chat about animals."],
                    "hypotheses": ["that a great name for a cat",
                                   "i don't want to talk about politics",
                                   "why did you call your cat this name?"],
                    }

    result = requests.post(url, json=request_data).json()
    gold_result = [{'batch': [{'isResponseComprehensible': 0.918, 'isResponseErroneous': 0.943,
                               'isResponseInteresting': 0.096, 'isResponseOnTopic': 0.301,
                               'responseEngagesUser': 0.231},
                              {'isResponseComprehensible': 0.684, 'isResponseErroneous': 0.911,
                               'isResponseInteresting': 0.005, 'isResponseOnTopic': 0.149,
                               'responseEngagesUser': 0.282},
                              {'isResponseComprehensible': 0.798, 'isResponseErroneous': 0.924,
                               'isResponseInteresting': 0.024, 'isResponseOnTopic': 0.242,
                               'responseEngagesUser': 0.387}]
                    }]
    assert result == gold_result, f'Got\n{result}\n, but expected:\n{gold_result}'
    print('Success')


if __name__ == '__main__':
    main()
