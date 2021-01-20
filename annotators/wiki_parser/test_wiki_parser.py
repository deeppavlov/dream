import requests


def main():
    url = 'http://0.0.0.0:8077/model'

    request_data = [{"parser_info": ["find_top_triplets"], "query": ["Q92735"]}]

    gold_results = [[[{'Q92735': [['Q92735', 'P31', 'Q5'],
                                  ['Q92735', 'P106', 'Q15976092'],
                                  ['Q92735', 'P106', 'Q1622272'],
                                  ['Q92735', 'P106', 'Q82594'],
                                  ['Q92735', 'P27', 'Q183'],
                                  ['Q92735', 'P569', '"+1963-01-17^^T"']]}]]

                    ]
    count = 0
    for data, gold_result in zip(request_data, gold_results):
        result = requests.post(url, json=data).json()
        if result == gold_result:
            count += 1
        else:
            print(f"Got {result}, but expected: {gold_result}")

    if count == len(request_data):
        print('Success')


if __name__ == '__main__':
    main()
