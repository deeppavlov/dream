import requests


def main():
    url = 'http://0.0.0.0:8078/model'
    
    request_data = [{"question_raw": ["Who was the first man in space?"]},
                    {"question_raw": ["Who played Sheldon Cooper in The Big Bang Theory?"]}]

    gold_results = [[['Yuri Gagarin', 0.9999731183052063, 29]],
                    [['James Joseph Parsons', 0.9999749660491943, 0]]
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
