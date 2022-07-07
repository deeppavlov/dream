import requests


true_requests = {
    "super_bowl": [
        "can you please uhhh so i can i keep saying i will go to super bowl",
        "hey alexa i did for the super bowl",
    ],
    "talk_about": [
        "tell me about the super bowl this year",
        "stop alexa tell me about super bowl twenty twenty",
        "i wanna talk about the super bowl",
        "let's talk about the super bowl",
        "do you wanna talk about the super bowl is gonna win",
    ],
    "fun_facts": ["do you know anything about the upcoming super bowl"],
    "what_about": ["super bowl", "the super bowl", "what about super bowl", "what about super bowl fifty four"],
    "what_time": [
        "alexa what time is the super bowl tomorrow now it's february second",
        "what time is the super bowl",
    ],
    "who_goes": [
        "who do you think is gonna be in the super bowl this year",
        "who do you predict will be in the super bowl twenty twenty",
        "alexa who's going to the super bowl",
        "alexa who's gonna go to the super bowl",
        "do you know who's playing in the super bowl",
        "tell me who's in the division playoffs for the super bowl",
        "who's going to super bowl forty fifty four",
        "who's playing in the super bowl",
        "who's playing in the super bowl this year",
        "who's playing super bowl fifty four",
        "who's playing super bowl twenty twenty",
        "who's your favorite in the super bowl",
    ],
    "who_wins": [
        "who do you think's gonna make it to the super bowl",
        "alexa who's gonna win the super bowl in cheeses the forty niners",
        "alexa who will win super bowl one hundred",
        "anything that's gonna win the super bowl",
        "gonna win the super bowl",
        "how do you think is gonna win the super bowl",
        "i listen let's talk about n. f. l. who do you think's gonna win the super bowl",
        "it's going to win the super bowl",
        "which team is most likely to win the super bowl",
        "which team will win the super bowl this year",
        "who are the niners win the super bowl you think",
        "who do you think is going to win the super bowl",
        "who do you think is gonna win the super bowl",
        "who do you think's gonna win the super bowl",
        "who do you think's gonna win the super bowl this year what's your thought",
        "who do you think will win the super bowl",
        "who do you think will win the super bowl this year",
        "who do you wanna win the super bowl",
        "who do you win the super bowl this year",
        "who is gonna win the super bowl",
        "who is gonna win the super bowl this year and your thoughts",
        "who is predicted to win the super bowl",
        "who's gonna win it was one of the super bowl",
        "who's gonna win the super bowl",
        "who's gonna win the super bowl in twenty twenty",
        "who's gonna win the super bowl the chiefs will forty niners",
        "who's gonna win the super bowl this year",
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
    url = "http://0.0.0.0:8051/respond"
    input_data = {
        "sentences": ["what do you like", "what do you like"],
    }
    for segment_name, segment_examples in true_requests.items():
        for example in segment_examples:
            input_data["sentences"] = [example]
            response = requests.post(url, json=input_data).json()
            assert response[0][0], f"segment_name: {segment_name}\nexample: {example}"
    for example in false_requests:
        input_data["sentences"] = [example]
        response = requests.post(url, json=input_data).json()
        assert not (response[0][0]), f"segment_name: false_segment\nexample: {example}"
    print("SUCCESS!")


if __name__ == "__main__":
    test_skill()
