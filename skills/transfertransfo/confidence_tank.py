import os

import numpy as np
import requests

TGT_URL = os.getenv("TGT_URL", "http://localhost/transfertransfo/")
N_REQUESTS = int(os.getenv("N_REQUESTS", 5))
OUT_FILE = int(os.getenv("OUT_FILE", "confidences.npy"))

personality = [
    "I am a socialbot.",
    "I live on Amazon Web Service.",
    "I was born during the Alexa Prize Challenge.",
    "I like talking to people.",
    "I love to meet new people.",
    "I like jazz music.",
    "I like listening music.",
    "I like watching movies and series.",
    "I like to play sports.",
    "I like to work out.",
    "I enjoy reading books.",
    "I love dogs, especially bulldog.",
    "I like cats, they are funny.",
    "I love hot-dogs.",
    "I like sushi.",
    "I like pizza and pasta.",
    "I do not like chocolate.",
    "I am never still.",
]

dialogs = [
    [
        "hello",
        "hi",
        "how are you",
        "i'm okay",
        "what are you do",
        "i am on amazon right now",
        "what kind of books do you read",
        "i love sci fi and sci fi fiction",
        "what else do you like",
        "i like watching netflix, netflix etc",
        "i love netflix but not netflix movies.",
        "what else do you like",
        "books mostly. what about you",
        "i am a programmer",
        "what kind of work do you do",
        "a software developer",
        "cool! do you have any pets",
        "no, i don't have any pets",
        "that is too bad",
        "what kind do you have",
        "dogs",
        "i don't have any",
        "that'sn't a problem",
        "what do you do for a living",
        "my name is alexa",
        "nice to meet you",
        "what do you do",
        "i work from home",
        "what city are you from",
        "cali, what about you",
        "i live on amazon",
        "nice",
        "what do you do in your spare time",
        "i enjoy listening to jazz",
        "what else do you like to do",
        "read",
        "i'm a bookworm",
        "nice! whats a bookworm do you publish",
        "have a good day",
        "goodbuy",
    ]
]


def history_gen(dialogs):
    for dialog in dialogs:
        for i in range(1, len(dialog) + 1):
            history = dialog[:i]
            yield history


confidences = []
for history in list(history_gen(dialogs)):
    response = {}
    for _ in range(N_REQUESTS):
        data = requests.post(TGT_URL, json={"personality": [personality], "utterances_histories": [history]}).json()[0]
        response[data[0]] = data[1]
    confidences.extend(response.values())

np.save(OUT_FILE, confidences)
