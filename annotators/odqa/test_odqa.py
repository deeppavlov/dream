import requests


def main():
    url = 'http://0.0.0.0:8078/model'

    request_data = [{"question_raw": ["Who played Sheldon Cooper in The Big Bang Theory?"],
                     "entity_substr": [["Sheldon Cooper", "The Big Bang Theory"]]},
                    {"question_raw": ["What is the capital of Germany?"],
                     "entity_substr": [["the capital", "Germany"]]},
                    {"question_raw": ["/alexa_stop_handler."], "entity_substr": [[]]},
                    {"question_raw": [" "], "entity_substr": [[]]}]

    gold_answers = ["Jim Parsons", "Everest", "", ""]
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
