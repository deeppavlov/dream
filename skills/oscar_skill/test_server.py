import requests


true_requests = {
    "oscars": [
        "what about the oscars nominations",
        "What do you know about Oscars nominations",
        "Tell me more about oscars nominations",
        "tell me about the best oscars picture",
        "tell me about the best oscars director",
        "tell me about the best oscars actor",
        "tell me about the best oscars actress",
        "tell me about the Oscars twenty nineteen",
        "tell me about the Oscars twenty twenty",
        "give me interesting facts about the oscars twenty nineteen",
        "give me interesting facts about the oscars twenty twenty",
        "who will win the oscars",
        "what about oscar",
        "tell me about the best oscars actor nomination",
    ],
    "directors": [
        "tell me something about martin scorsese",
        "tell me something about todd phillips",
        "tell me something about sam mendes",
        "tell me something about quentin tarantino",
        "tell me something about bong joonho",
    ],
    "actors": [
        "tell me something about leonardo dicaprio",
        "tell me something about joaquin phoenix",
        "tell me something about tom hanks",
        "tell me something about brad pitt",
        "tell me something about Joker actor",
    ],
    "actresses": [
        "tell me something about laura dern",
        # "tell me something about jennifer lopez",
        "tell me something about florence pugh",
        "tell me something about margaret qualley",
    ],
    "films": [
        "tell me something about Ford v Ferrari",
        "tell me something about The Irishman movie",
        "tell me something about Jojo Rabbit",
        "tell me something about Joker",
        "tell me something about Little Women",
        "tell me something about Marriage Story",
        "tell me something about nineteen seventeen",
        "tell me something about Once Upon a Time in Hollywood",
        "tell me something about the parasite movie",
        "tell me something about Joker on Oscors",
    ],
}

false_requests = [
    "the pro bowl",
    "i wanna talk about the the pro bowl",
    "i don't know if the rose bowl parade is be replayed today",
    "who will win the twenty twenty rose bowl",
    "i like to bowl and i like to",
    "just wanna know if they're the pro bowl team that wins if they get more than money",
    "in a fish bowl",
    "no i can bowl",
    "do you think bowling is a cool sport",
    "then mission in toilet paper bowl",
    "when does auburn play their next bowl game",
    "your baby bowl is that problem what are you doing",
    "please can you gave is such a dick you started cyberbowling me after he got expelled",
    "when is the college football gatorbowl on",
    "alexa what book college football bowl games are on today",
]


def test_skill():
    url = "http://0.0.0.0:8055/respond"
    input_data = {
        "sentences": ["what do you like", "what do you like"],
    }
    for segment_name, segment_examples in true_requests.items():
        for example in segment_examples:
            input_data["sentences"] = [example]
            response = requests.post(url, json=input_data).json()
            # print(f"Q:{example}\nA:{response[0][0]}\n")
            assert response[0][0], f"segment_name: {segment_name}\nexample: {example}"
    for example in false_requests:
        input_data["sentences"] = [example]
        response = requests.post(url, json=input_data).json()
        assert not (response[0][0]), f"segment_name: false_segment\nexample: {example}"
    print("SUCCESS!")


if __name__ == "__main__":
    test_skill()
