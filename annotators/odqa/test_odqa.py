import requests


def main():
    url = 'http://0.0.0.0:8078/model'

    request_data = [{"question_raw": ["Who played Sheldon Cooper in The Big Bang Theory?"]},
                    {"question_raw": ["What are highest mountains in the world?"]}]

    gold_answers = ["Jim Parsons", "The Himalayas"]
    count = 0
    for data, gold_answer in zip(request_data, gold_answers):
        result = requests.post(url, json=data).json()
        res_ans = result[0]["answer"]
        if res_ans == gold_answer:
            count += 1
        else:
            print(f"Got {result}, but expected: {gold_answer}")

    if count == len(request_data):
        print('Success')


if __name__ == '__main__':
    main()
