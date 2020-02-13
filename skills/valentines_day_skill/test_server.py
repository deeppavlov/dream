import requests


true_requests = {
    "what_is_love": ["what is love"],
    "about_love": ["what is the love", "what do you know about the love", "tell me about the love"],
    "do_you_love": ["do you love"],
    "who_you_love": ["who do you love"],
    "received_card": ["did you get a valentine"],
    "valentines_day": [
        "what is valentines day",
        "what do you know about the valentines day",
        "tell me about the valentines day",
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
    url = "http://0.0.0.0:8058/respond"
    input_data = {}
    for segment_name, segment_examples in true_requests.items():
        for example in segment_examples:
            input_data["sentences"] = [example]
            response = requests.post(url, json=input_data).json()
            print(f"Q:{example}\nA:{response[0][0]}\n")
            assert response[0][0], f"segment_name: {segment_name}\nexample: {example}"
    for example in false_requests:
        input_data["sentences"] = [example]
        response = requests.post(url, json=input_data).json()
        assert not (response[0][0]), f"segment_name: false_segment\nexample: {example}"
    print("SUCCESS!")


if __name__ == "__main__":
    test_skill()
