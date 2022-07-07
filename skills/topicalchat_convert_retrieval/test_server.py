import requests


topics = {
    "topics": [
        {
            "text": [
                "Art_Event",
                "Celebrities",
                "Entertainment",
                "Fashion",
                "Food_Drink",
                "Games",
                "Literature",
                "Math",
                "Movies_TV",
                "Music",
                "News",
                "Other",
                "Pets_Animals",
                "Phatic",
                "Politics",
                "Psychology",
                "Religion",
                "SciTech",
                "Sex_Profanity",
                "Sports",
                "Travel_Geo",
                "Weather_Time",
            ]
        }
    ],
    "dialogact_topics": [
        [
            "Other",
            "Interactive",
            "Phatic",
            "Entertainment_Movies",
            "Science_and_Technology",
            "Sports",
            "Entertainment_Music",
            "Entertainment_General",
            "Politics",
            "Entertainment_Books",
        ]
    ],
}


true_requests = {
    "movie": [
        {"utterances_histories": [["what you know about movie"]], "response": ["not much but i love watching movies"]}
    ],
    "music": [
        {
            "utterances_histories": [["what you know about music"]],
            "response": [
                "Well i look up odd facts about google and sometimes look up musicians and concerts",
                "i am good i love music do you",
            ],
        }
    ],
    "book": [{"utterances_histories": [["what you know about book"]], "response": ["i read a lot what about you"]}],
    "entertainment": [
        {
            "utterances_histories": [["what you know about entertainment"]],
            "response": [
                "not much but i love watching movies",
                "I do like to watch TV its one of my favorite forms of entertainment",
            ],
        }
    ],
    "fashion": [
        {
            "utterances_histories": [["what you know about fashion"]],
            "response": [
                "i dress up , i like fashion shows",
                "Yes I know a lot about clothing actually. In fact I'm wearing some right now LOL what about you",
            ],
        }
    ],
    "politics": [
        {
            "utterances_histories": [["what you know about politics"]],
            "response": [
                "i am passionate about politics , so i indulge in those topics , wbu ?",
                "Sometimes I follow politics. What about you?",
            ],
        }
    ],
    "science_technology": [
        {
            "utterances_histories": [["what you know about science"]],
            "response": ["i do not i study science mostly its fascinating"],
        }
    ],
    "sport": [
        {
            "utterances_histories": [["what you know about sport"]],
            "response": ["I am great what about you? do you like football?", "i am great just never liked sports"],
        }
    ],
    "animals": [
        {
            "utterances_histories": [["what you know about animals"]],
            "response": [
                "my dog is just my pet but I do like learning about interesting facts about them",
                "i am literally obsessed with animals",
            ],
        }
    ],
}


def test_skill():
    url = "http://0.0.0.0:8060/respond"
    for topic_name, topic_examples in true_requests.items():
        for example in topic_examples:
            example.update(topics)
            example["utterances_histories"] = [["hi", "how are you", "i am fine"] + example["utterances_histories"][0]]
            response = requests.post(url, json=example).json()
            print(response)
            assert response[0][0] in example["response"], f"topic_name: {topic_name}\nexample: {example}"
    print("SUCCESS!")


if __name__ == "__main__":
    test_skill()
