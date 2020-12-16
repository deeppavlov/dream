import requests


def main():
    url = 'http://0.0.0.0:8075/model'
    
    request_data = [{"entity_substr": [["Forrest Gump"]],
                     "template": [""],
                     "context": ["Who directed Forrest Gump?"]},
                    {"entity_substr": [["Robert Lewandowski"]],
                     "template": [""],
                     "context": ["What team Robert Lewandowski plays for?"]}]

    gold_results = [[[[['Q134773', 'Q3077690', 'Q552213', 'Q5365088', 'Q17006552']], [[0.02, 0.02, 0.02, 0.02, 0.02]]]],
                    [[[['Q151269', 'Q16596664', 'Q1608729', 'Q1803446', 'Q11834963']], [[0.02, 0.02, 0.01, 0.01, 0.01]]]]]
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
