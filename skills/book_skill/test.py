import requests
import json
from copy import deepcopy


def get_input_json(fname):
    with open(fname, "r") as f:
        res = json.load(f)
    # if len(res[0]['utterances'])%2==0:
    #    res[0]['utterances']=res[0]['utterances'][:-1]
    return {"dialogs": res}


def slice_(input_data, i):
    tmp_data = deepcopy(input_data)
    tmp_data['dialogs'][0]['utterances'] = input_data['dialogs'][0]['utterances'][:i]
    return tmp_data


def main_test():
    url = 'http://0.0.0.0:8032/book_skill'
    input_data = get_input_json("test_configs/test_dialog.json")
    sliced_data = [slice_(input_data, i) for i in range(1, 21, 2)]
    responses = [requests.post(url, json=tmp).json()[0][0] for tmp in sliced_data]
    gold_phrases = ["I've read it. It's an amazing book! Would you like to know some facts about it?",
                    "The Little Prince is a novella by French aristocrat, writer, and aviator " + (
                        "Antoine de Saint-Exupéry. It was first published in English and French in the US ") + (
                        "by Reynal & Hitchcock in April 1943, and posthumously in France following the ") + (
                        "liberation of France as Saint-Exupéry's works had been banned by the Vichy Regime."),
                    'My favourite book is "The Old Man and the Sea" by Ernest Hemingway.',
                    "OK, let's talk about books. Do you love reading?",
                    "That's great. What is the last book you have read?",
                    "Interesting. Have you read ",
                    # This should be a beginning of the response - response needs to be randomized
                    "I've also read it. It's an amazing book!",
                    'What is your favorite book genre?',
                    'Amazing! Have you read The Testaments ? And if you have read it, what do you think about it?',
                    json.load(open('bookreads_data.json', 'r'))[0]['fiction']['description']]
    for i in range(len(responses)):
        assert gold_phrases[i] in responses[i], str(i) + ' ' + str(responses[i])


if __name__ == '__main__':
    main_test()
