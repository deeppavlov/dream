import requests


def main():
    url = 'http://0.0.0.0:8100/model'

    request_data = [{"human_sentences": ["Who played Sheldon Cooper in The Big Bang Theory?"],
                     "dialog_history": ["Who played Sheldon Cooper in The Big Bang Theory?"],
                     "entity_substr": [["Sheldon Cooper", "The Big Bang Theory"]],
                     "entity_pages": [[["Sheldon Cooper"], ["The Big Bang Theory"]]]},
                    {"human_sentences": ["What is the capital of Germany?"],
                     "dialog_history": ["What is the capital of Germany?"],
                     "entity_substr": [["the capital", "Germany"]],
                     "entity_pages": [[["Capital"], ["Germany"]]]},
                    {"human_sentences": ["/alexa_stop_handler."], "dialog_history": [""], "entity_substr": [[]]},
                    {"human_sentences": [" "], "dialog_history": [""], "entity_substr": [[]]}]

    gold_results = [True, True, False, False]
    count = 0
    for data, gold_result in zip(request_data, gold_results):
        result = requests.post(url, json=data).json()
        if (len(result[0]) > 0) == gold_result:
            count += 1
        else:
            print(f"Got {result}, but expected: {gold_result}")

    assert count == len(request_data)
    print('Success')


if __name__ == '__main__':
    main()
