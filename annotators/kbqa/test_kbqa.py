import requests


def main():
    url = 'http://0.0.0.0:8072/model'

    request_data = [{"x_init": ["Who is Donald Trump?"]},
                    {"x_init": ["How old is Donald Trump?"]}]

    gold_results = [[['Donald Trump is 45th and current president of the United States.', 1.0]],
                    [['Donald Trump is 75 years old.', 1.0]]
                    ]
    count = 0
    for data, gold_result in zip(request_data, gold_results):
        result = requests.post(url, json=data).json()["kbqa_res"]
        res_ans, res_conf = result[0]
        gold_ans, gold_conf = gold_result[0]
        if res_ans == gold_ans and res_conf == gold_conf:
            count += 1
        else:
            print(f"Got {result}, but expected: {gold_result}")

    if count == len(request_data):
        print('Success')


if __name__ == '__main__':
    main()
