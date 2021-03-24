import requests
import json
from copy import deepcopy


def slice_(input_data, i):
    tmp_data = deepcopy(input_data)
    tmp_data['dialogs'][0]['human_utterances'] = input_data['dialogs'][0]['human_utterances'][:i]
    tmp_data['dialogs'][0]['bot_utterances'] = input_data['dialogs'][0]['bot_utterances'][:i - 1]
    past_phrases = [j['text'] for ii, j in enumerate(input_data['dialogs'][0]['human_utterances']) if ii % 2 == 1]
    tmp_data['dialogs'][0]['human']['attributes'] = {'book_skill': {'used_phrases': past_phrases}}
    return tmp_data


def main_test():
    url = 'http://0.0.0.0:8032/book_skill'
    input_data = json.load(open("test_configs/test_dialog.json", "r"))
    sliced_data = [slice_(input_data, i) for i in range(1, 10)]
    gold_phrases = ["I've read it. It's an amazing book! Would you like to know some facts about it?",
                    "",  # As CobotQA doesn't always work
                    'My favourite book is "The Old Man and the Sea" by Ernest Hemingway.',
                    "OK, let's talk about books. Do you love reading?",
                    "That's great. What is the last book you have read?",
                    "Interesting. Have you read",
                    "It's an amazing book! Do you know when it was first published?",
                    # This should be a beginning of the response - response needs to be randomized
                    'What is your favorite book genre?',
                    'Amazing! Have you read The Testaments? And if you have read it, what do you think about it?',
                    json.load(open('bookreads_data.json', 'r'))[0]['fiction']['description']]
    for i in range(len(sliced_data)):
        response = requests.post(url, json=sliced_data[i]).json()[0][0]
        if i != 1:  # As CobotQA doesn't always work
            assert len(response) > 0
        assert response in gold_phrases[i] or gold_phrases[i] in response, '*'.join([response, gold_phrases[i]])
    print('TESTS FOR BOOK SKILL PASSED')
    return 0


if __name__ == '__main__':
    main_test()
