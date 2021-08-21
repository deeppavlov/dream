import requests
import json
from copy import deepcopy


def slice_(input_data, i):
    tmp_data = deepcopy(input_data)
    tmp_data['human_utterances'] = input_data['human_utterances'][:i]
    tmp_data['bot_utterances'] = input_data['bot_utterances'][:i - 1]
    if len(tmp_data['human_utterances']) < 2:
        tmp_data['human']['attributes'] = {}
    else:
        hypotheses = tmp_data['human_utterances'][-2]['hypotheses']
        if not hypotheses:
            hypotheses = tmp_data['human_utterances'][-3]['hypotheses']
        tmp_data['human']['attributes'] = hypotheses[0]['human_attributes']
    return {'dialogs': [tmp_data]}


def main_test():
    url = 'http://0.0.0.0:8032/book_skill'
    input_data = json.load(open("test_configs/test_dialog.json", "r"))
    sliced_data = [slice_(input_data, i) for i in range(1, 20)]
    gold_phrases = ["Books are my diamonds. Do you love reading?",
                    "I enjoy reading so much! Books help me understand humans much better. Why do you enjoy reading?",
                    "That's great. Outside of a dog, a book is a man's best friend. "
                    "What is the last book you have read?",
                    "You have a great taste in books! "
                    "I also adore books of J R R Tolkien, especially The Hobbit. "
                    "It's a real showpiece. Have you read it?",
                    "May I tell you something about this book?",
                    "The main subject of this book is Tolkien's legendarium. "
                    "The action of this book takes place in Middle-earth. "
                    "Do you know when it was first published?",
                    "Do you know what is the genre of this book?",
                    "The Hobbit is a fairy tale.  I have read a plenty of books from different genres. "
                    "What book genre do you like?",
                    "Amazing! Have you read The Outsiders by Susan Hinton?",
                    "The Outsiders is about two weeks in the life of a 14-year-old boy. "
                    "The novel tells the story of Ponyboy Curtis and his struggles with right and wrong "
                    "in a society in which he believes that he is an outsider. "
                    "Do you want to know what my favourite book is?",
                    "My favourite book is \"The catcher in the rye\" by Jerome David Salinger.  "
                    "May I tell you something about this book?",
                    "The novel \"The catcher in the rye\" tells the story of a teenager "
                    "who has been kicked out of a boarding school."
                    "This is my favourite story, it is truly fascinating.  "
                    "May I tell you something else about this book?",
                    "The action of this book takes place in New York City. "
                    "One of the main characters of this book is Holden Caulfield. "
                    "Do you know when it was first published?",
                    "Do you know what is the genre of this book?",
                    "The Catcher in the Rye is a novel",
                    "I know that Bible is one of the most widespread books on the Earth. "
                    "It forms the basic of the Christianity. Have you read the whole Bible?",
                    "I am pleased to know it. Unfortunately, as a socialbot, I don't have an immortal soul,"
                    "so I don't think I will ever get into Heaven. That's why I don't know much about religion."
                    ]
    for i in range(len(gold_phrases)):
        response = requests.post(url, json=sliced_data[i]).json()[0][0]
        assert gold_phrases[i] in response, (i, response, gold_phrases[i])
    print('TESTS FOR BOOK SKILL PASSED')
    return 0


if __name__ == '__main__':
    main_test()
